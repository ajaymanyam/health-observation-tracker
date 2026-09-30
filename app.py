"""
Health Observation Tracker
A Streamlit web application to help patients and caregivers record, track,
and organize repeated visible health observations over time with multimodal AI
and WhatsApp sharing via Twilio.
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Tuple

import streamlit as st
from PIL import Image

# Google GenAI SDK (official google-genai)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Twilio SDK
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Health Observation Tracker",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Styling
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global Styles */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.25rem;
    }
    .disclaimer-box {
        background-color: #f0fdf4;
        border-left: 4px solid #16a34a;
        padding: 0.85rem 1.1rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
        font-size: 0.92rem;
        color: #166534;
    }
    .disclaimer-warning {
        background-color: #eff6ff;
        border-left: 4px solid #2563eb;
        padding: 0.85rem 1.1rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
        font-size: 0.92rem;
        color: #1e40af;
    }
    .timeline-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .timeline-badge {
        display: inline-block;
        background-color: #e0e7ff;
        color: #3730a3;
        font-weight: 600;
        font-size: 0.82rem;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        margin-bottom: 0.75rem;
    }
    .summary-card {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    .status-pill-green {
        display: inline-block;
        background-color: #dcfce7;
        color: #15803d;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .status-pill-gray {
        display: inline-block;
        background-color: #f1f5f9;
        color: #64748b;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Configuration & Secret Helpers
# -----------------------------------------------------------------------------
def get_secret(key: str, default: str = "") -> str:
    """Safely retrieve a secret from st.secrets or os.environ."""
    try:
        if key in st.secrets:
            val = st.secrets[key]
            if val is not None:
                return str(val).strip()
    except Exception:
        pass
    return os.environ.get(key, default).strip()


GEMINI_API_KEY_SECRET = get_secret("GEMINI_API_KEY")
TWILIO_ACCOUNT_SID = get_secret("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = get_secret("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = get_secret("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TWILIO_CONTENT_SID = get_secret("TWILIO_CONTENT_SID")

# -----------------------------------------------------------------------------
# Gemini Client Caching
# -----------------------------------------------------------------------------
@st.cache_resource
def get_gemini_client(api_key: str):
    """
    Creates and caches the Google Gemini client.
    Cached across interactions using st.cache_resource.
    """
    if not GENAI_AVAILABLE:
        raise ImportError("google-genai package is not installed.")
    return genai.Client(api_key=api_key)


def is_placeholder(val: str) -> bool:
    """Checks if a secret value is just a placeholder."""
    if not val:
        return True
    low = val.lower().strip()
    return (
        low.startswith("your-")
        or "your-gemini" in low
        or "your_gemini" in low
        or "your-account" in low
        or "your-auth" in low
        or "your-content" in low
    )


def get_effective_gemini_api_key() -> str:
    """Returns the effective Gemini API key from secrets or user input."""
    if GEMINI_API_KEY_SECRET and not is_placeholder(GEMINI_API_KEY_SECRET):
        return GEMINI_API_KEY_SECRET
    return st.session_state.get("user_gemini_api_key", "").strip()


def display_gemini_error(e: Exception, api_key: str):
    """Formats and displays user-friendly error messages for Gemini issues."""
    clean_err = str(e)
    if api_key:
        clean_err = clean_err.replace(api_key, "[REDACTED]")
    if "API_KEY_INVALID" in clean_err or "API key not valid" in clean_err:
        st.error(
            "🔑 **Invalid Gemini API Key**: Google returned `API_KEY_INVALID`.\n\n"
            "This happens when `.streamlit/secrets.toml` still contains the placeholder text `\"your-gemini-api-key-here\"` "
            "or the API key was copied incompletely.\n\n"
            "👉 **How to fix:**\n"
            "1. Generate a free API key at [Google AI Studio](https://aistudio.google.com/).\n"
            "2. Open `.streamlit/secrets.toml` and replace `your-gemini-api-key-here` with your key (e.g. `AIzaSy...`).\n"
            "3. Or enter it directly in the **Gemini API Key** field in the left sidebar!"
        )
    else:
        st.error(f"Gemini API Error: {clean_err}")


def init_gemini_chat(client: "genai.Client"):
    """
    Initializes a Gemini chat session configured with the SYSTEM_PROMPT.
    Tries gemini-3.5-flash first, falling back to gemini-3.8-flash or gemini-3.7-flash.
    """
    candidate_models = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-2.5-flash"]
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.3,
    )
    last_error = None
    for model_name in candidate_models:
        try:
            chat = client.chats.create(
                model=model_name,
                config=config,
            )
            return chat, model_name
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"Could not initialize Gemini chat session: {last_error}")


def send_chat_message_with_retry(chat, message_contents, max_retries: int = 2):
    """Sends a message to the active chat session with automatic retry on temporary demand spikes."""
    for attempt in range(max_retries + 1):
        try:
            return chat.send_message(message_contents)
        except Exception as e:
            err_str = str(e)
            if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < max_retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            raise e

# -----------------------------------------------------------------------------
# Twilio WhatsApp Sender Helper
# -----------------------------------------------------------------------------
def send_whatsapp_summary(
    to_number: str,
    user_name: str,
    summary_text: str,
) -> Tuple[bool, str]:
    """
    Sends the observation summary to the user's WhatsApp number using Twilio.
    Supports Twilio Content Template with fallback to direct body.
    """
    if not TWILIO_AVAILABLE:
        return False, "Twilio library is not installed."

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return False, "Twilio Account SID or Auth Token is not configured."

    # Format phone number for WhatsApp
    clean_to = to_number.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not clean_to.startswith("whatsapp:"):
        if not clean_to.startswith("+"):
            clean_to = f"+{clean_to}"
        clean_to = f"whatsapp:{clean_to}"

    clean_from = TWILIO_WHATSAPP_FROM.strip()
    if not clean_from.startswith("whatsapp:"):
        clean_from = f"whatsapp:{clean_from}"

    try:
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Attempt with Twilio Content Template if a real Content SID is configured
        if TWILIO_CONTENT_SID and not is_placeholder(TWILIO_CONTENT_SID):
            try:
                variables = {
                    "1": user_name,
                    "2": summary_text[:1200],
                }
                msg = client.messages.create(
                    from_=clean_from,
                    to=clean_to,
                    content_sid=TWILIO_CONTENT_SID,
                    content_variables=json.dumps(variables),
                )
                return True, f"Summary sent via WhatsApp Content Template! (SID: {msg.sid})"
            except Exception as template_err:
                # If Content Template fails (e.g. template variables mismatch), fallback to direct body
                pass

        # Standard WhatsApp message body
        formatted_body = (
            f"🩺 *Health Observation Tracker Summary*\n\n"
            f"👤 *Patient / Caregiver:* {user_name}\n"
            f"📅 *Generated:* {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n\n"
            f"{summary_text}\n\n"
            f"---\n"
            f"⚠️ *Notice:* This summary records visible observations for discussion "
            f"with your healthcare professional and is not a medical diagnosis."
        )
        msg = client.messages.create(
            from_=clean_from,
            to=clean_to,
            body=formatted_body,
        )
        return True, f"Summary sent successfully to WhatsApp! (SID: {msg.sid})"

    except Exception as e:
        # Sanitize error to avoid leaking credentials
        err_msg = str(e)
        if TWILIO_AUTH_TOKEN:
            err_msg = err_msg.replace(TWILIO_AUTH_TOKEN, "[REDACTED]")
        if TWILIO_ACCOUNT_SID:
            err_msg = err_msg.replace(TWILIO_ACCOUNT_SID, "[REDACTED]")
        if "422" in err_msg or "verified recipient" in err_msg:
            err_msg += (
                "\n\n👉 **How to fix this with Twilio Trial:**\n"
                "1. **Verified Caller IDs**: Go to Twilio Console > **Phone Numbers** > **Manage** > **Verified Caller IDs** and add your phone number.\n"
                "2. **WhatsApp Sandbox**: Twilio free trial numbers (like standard US numbers) cannot send WhatsApp messages directly. Change `TWILIO_WHATSAPP_FROM` to `whatsapp:+14155238886` in `.streamlit/secrets.toml`.\n"
                "3. **Join Sandbox**: From your phone, send your Twilio sandbox join keyword (e.g. `join <keyword>`) on WhatsApp to `+1 415 523 8886`."
            )
        elif "ContentSid" in err_msg:
            err_msg = (
                "Twilio Trial account restriction: Twilio requires an upgraded/paid subscription to create and use custom WhatsApp Content Templates (`ContentSid`).\n\n"
                "👉 **Instant free solution:** Use the **'📲 Send directly via WhatsApp'** button below to deliver your summary straight to your WhatsApp app or WhatsApp Web for free without needing a Twilio subscription!"
            )
        return False, f"Twilio WhatsApp notice: {err_msg}"

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False

if "name" not in st.session_state:
    st.session_state.name = ""

if "whatsapp_number" not in st.session_state:
    st.session_state.whatsapp_number = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "observations" not in st.session_state:
    st.session_state.observations = []

if "chat" not in st.session_state:
    st.session_state.chat = None

if "chat_model_name" not in st.session_state:
    st.session_state.chat_model_name = ""

if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""

if "user_gemini_api_key" not in st.session_state:
    st.session_state.user_gemini_api_key = ""

# -----------------------------------------------------------------------------
# Sidebar: User Info, Configuration & Actions
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🩺 Health Tracker")
    st.caption("Observation Documentation Assistant")
    st.markdown("---")

    # API Key Configuration if not in secrets.toml
    eff_key = get_effective_gemini_api_key()
    if not eff_key:
        st.subheader("🔑 Gemini API Key")
        if GEMINI_API_KEY_SECRET and is_placeholder(GEMINI_API_KEY_SECRET):
            st.info("ℹ️ `.streamlit/secrets.toml` currently has the placeholder text `\"your-gemini-api-key-here\"`. Replace it in the file or enter your real key below:")
        api_input = st.text_input(
            "Enter Gemini API Key",
            type="password",
            placeholder="AIzaSy...",
            help="Your API key is used only in memory and never stored permanently.",
        )
        if api_input:
            st.session_state.user_gemini_api_key = api_input.strip()
            st.success("API Key saved for current session.")
            st.rerun()

    # User Profile Info
    if st.session_state.onboarded:
        st.subheader("👤 User Profile")
        st.markdown(f"**Name:** {st.session_state.name}")
        st.markdown(f"**WhatsApp:** {st.session_state.whatsapp_number}")

        with st.expander("✏️ Edit Profile"):
            new_name = st.text_input("Name", value=st.session_state.name, key="edit_name")
            new_phone = st.text_input(
                "WhatsApp Number",
                value=st.session_state.whatsapp_number,
                key="edit_phone",
            )
            if st.button("Update Profile"):
                st.session_state.name = new_name.strip()
                st.session_state.whatsapp_number = new_phone.strip()
                st.success("Profile updated.")
                st.rerun()

        st.markdown("---")

    # Service Status Badges
    st.subheader("⚙️ System Status")
    if eff_key:
        st.markdown('Gemini AI: <span class="status-pill-green">Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('Gemini AI: <span class="status-pill-gray">API Key Needed</span>', unsafe_allow_html=True)

    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        st.markdown('Twilio WhatsApp: <span class="status-pill-green">Configured</span>', unsafe_allow_html=True)
    else:
        st.markdown('Twilio WhatsApp: <span class="status-pill-gray">Local Test Mode</span>', unsafe_allow_html=True)

    # Session Statistics
    if st.session_state.onboarded:
        st.markdown("---")
        st.subheader("📊 Session Activity")
        st.metric("Recorded Observations", len(st.session_state.observations))
        st.metric("Total Messages", len(st.session_state.messages))

        # Reset Session Button
        if st.button("🔄 Start New Session", help="Clears conversation and observations for this session"):
            st.session_state.onboarded = False
            st.session_state.name = ""
            st.session_state.whatsapp_number = ""
            st.session_state.messages = []
            st.session_state.observations = []
            st.session_state.chat = None
            st.session_state.summary_text = ""
            st.rerun()

# -----------------------------------------------------------------------------
# Onboarding View
# -----------------------------------------------------------------------------
if not st.session_state.onboarded:
    st.markdown('<div class="main-header">🩺 Health Observation Tracker</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Record, organize, and monitor visible health observations over time with multimodal AI.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="disclaimer-warning">
            <strong>ℹ️ Documentation & Communication Assistant</strong><br>
            This application is designed solely to help patients and caregivers objectively document visible health observations 
            and communicate clearly with healthcare providers. It <strong>does not diagnose</strong> medical conditions, 
            prescribe medications, or replace professional medical care.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("👋 Welcome! Let's get started.")
    st.write("Please provide your name and WhatsApp number to begin your session.")

    with st.form("onboarding_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            name_input = st.text_input(
                "Patient / Caregiver Name *",
                placeholder="e.g., Jane Doe",
                help="The name used to personalize your observation records.",
            )
        with col2:
            phone_input = st.text_input(
                "WhatsApp Number *",
                placeholder="e.g., +1 555 123 4567",
                help="Include country code (e.g. +1 for US, +44 for UK, +91 for India).",
            )

        submit_onboarding = st.form_submit_button("Start Tracking Observations", type="primary")

        if submit_onboarding:
            if not name_input.strip():
                st.error("Please enter your name to continue.")
            elif not phone_input.strip():
                st.error("Please enter your WhatsApp phone number to continue.")
            else:
                # Save profile in session state
                st.session_state.name = name_input.strip()
                st.session_state.whatsapp_number = phone_input.strip()
                st.session_state.onboarded = True

                # Initialize conversation history with welcome message
                welcome_text = WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name)
                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": welcome_text,
                        "image": None,
                        "timestamp": datetime.now().strftime("%I:%M %p"),
                    }
                ]
                st.session_state.observations = []

                # Attempt to initialize Gemini chat session if API key is available
                api_key = get_effective_gemini_api_key()
                if api_key and GENAI_AVAILABLE:
                    try:
                        client = get_gemini_client(api_key)
                        chat, model_name = init_gemini_chat(client)
                        st.session_state.chat = chat
                        st.session_state.chat_model_name = model_name
                    except Exception as e:
                        st.warning(f"Could not connect to Gemini AI: {e}")

                st.rerun()

    st.stop()

# -----------------------------------------------------------------------------
# Main Application View (After Onboarding)
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">🩺 Health Observation Tracker</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-header">Active Session for <strong>{st.session_state.name}</strong> • WhatsApp: <code>{st.session_state.whatsapp_number}</code></div>',
    unsafe_allow_html=True,
)

# Safety notice banner
st.markdown(
    """
    <div class="disclaimer-box">
        <strong>🛡️ Safe Health Tracking Notice:</strong> All AI descriptions describe visible characteristics only. 
        The assistant does not make diagnoses or recommend treatments. If you experience severe symptoms or discomfort, 
        please consult a qualified healthcare professional promptly.
    </div>
    """,
    unsafe_allow_html=True,
)

# Verify Gemini API key is available
api_key = get_effective_gemini_api_key()
if not api_key:
    st.error(
        "⚠️ Gemini API Key is missing. Please enter your Gemini API Key in the left sidebar "
        "or define `GEMINI_API_KEY` in `.streamlit/secrets.toml` to enable AI visual analysis and conversation."
    )

# Ensure chat session is initialized if key is present
if api_key and GENAI_AVAILABLE and st.session_state.chat is None:
    try:
        client = get_gemini_client(api_key)
        chat, model_name = init_gemini_chat(client)
        st.session_state.chat = chat
        st.session_state.chat_model_name = model_name
    except Exception as e:
        st.error(f"Failed to initialize Gemini AI session: {e}")

# -----------------------------------------------------------------------------
# Section 1: Observation Assistant (Upload & Record)
# -----------------------------------------------------------------------------
st.markdown("### 📸 Observation Assistant")
st.write("Record a new visible health observation. You may provide a photo, written notes, or both.")

with st.container():
    upload_col, note_col = st.columns([1, 1])

    with upload_col:
        uploaded_image_file = st.file_uploader(
            "Upload Photo (JPG, JPEG, PNG)",
            type=["jpg", "jpeg", "png"],
            key="current_observation_photo",
            help="Clear, well-lit photos of the visible area help describe observable details accurately.",
        )
        loaded_image: Optional[Image.Image] = None
        if uploaded_image_file is not None:
            try:
                loaded_image = Image.open(uploaded_image_file)
                st.image(loaded_image, caption="Uploaded Observation Photo", use_container_width=True)
            except Exception as img_err:
                st.error("Invalid image file. Please upload a valid JPG or PNG photo.")
                loaded_image = None

    with note_col:
        user_written_note = st.text_area(
            "What did you notice?",
            placeholder="Example: Noticed a 2cm circular pink patch on left forearm. Started 2 days ago, feels mildly itchy, no warmth.",
            height=160,
            key="current_observation_note",
        )

    submit_obs_col, info_obs_col = st.columns([1, 2])
    with submit_obs_col:
        record_button = st.button("Record Observation & Analyze", type="primary", use_container_width=True)

    if record_button:
        # Validate that at least one input is provided
        has_image = loaded_image is not None
        has_note = bool(user_written_note.strip())

        if not has_image and not has_note:
            st.warning("⚠️ Please upload a photo, write an observation note, or both before submitting.")
        elif not api_key:
            st.error("Cannot analyze observation: Gemini API Key is missing. Please provide a key in the sidebar.")
        elif st.session_state.chat is None:
            st.error("AI Assistant is not ready. Please check your Gemini API key.")
        else:
            with st.spinner("Analyzing visible characteristics with Gemini AI..."):
                try:
                    # Construct message parts for Gemini
                    contents = []
                    if has_image:
                        contents.append(loaded_image)

                    prompt_parts = []
                    prompt_parts.append(f"Recorded by: {st.session_state.name}")
                    prompt_parts.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")

                    if has_note:
                        prompt_parts.append(f"User Written Note: '{user_written_note.strip()}'")

                    if has_image and has_note:
                        prompt_parts.append(
                            "Instructions: The user has provided an observation photo and note. "
                            "Carefully describe what is visibly observable in the image (color, margins, texture, swelling, size comparison if applicable). "
                            "Cross-reference neutrally with the user's note. Clearly communicate uncertainty. "
                            "Do not make any medical diagnosis or recommend medication/treatment."
                        )
                    elif has_image:
                        prompt_parts.append(
                            "Instructions: The user has uploaded an observation photo without written notes. "
                            "Carefully describe what is visibly observable in the image in neutral, objective language. "
                            "Clearly communicate uncertainty. Suggest what details the user may want to note down. "
                            "Do not make any medical diagnosis or recommend medication/treatment."
                        )
                    else:
                        prompt_parts.append(
                            "Instructions: The user recorded a written observation without an image. "
                            "Acknowledge the note neutrally, help organize the key descriptive elements, "
                            "and suggest what visible signs they should monitor over time to share with their doctor. "
                            "Do not make any medical diagnosis or recommend medication/treatment."
                        )

                    contents.append("\n\n".join(prompt_parts))

                    # Send to Gemini Chat Session to preserve session memory
                    response = send_chat_message_with_retry(st.session_state.chat, contents)
                    ai_response_text = response.text

                    timestamp_str = datetime.now().strftime("%b %d, %Y - %I:%M %p")

                    # Record in session observations timeline
                    obs_entry = {
                        "timestamp": timestamp_str,
                        "user_note": user_written_note.strip() if has_note else "No written note provided",
                        "image": loaded_image,
                        "ai_observation": ai_response_text,
                    }
                    st.session_state.observations.append(obs_entry)

                    # Add user entry to chat messages
                    user_display_msg = user_written_note.strip() if has_note else "Uploaded observation photo"
                    st.session_state.messages.append(
                        {
                            "role": "user",
                            "content": f"**[New Observation Recorded]**\n\n{user_display_msg}",
                            "image": loaded_image,
                            "timestamp": datetime.now().strftime("%I:%M %p"),
                        }
                    )

                    # Add AI response to chat messages
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": ai_response_text,
                            "image": None,
                            "timestamp": datetime.now().strftime("%I:%M %p"),
                        }
                    )

                    st.success("✅ Observation recorded and analyzed successfully!")
                    st.rerun()

                except Exception as e:
                    display_gemini_error(e, api_key)

# -----------------------------------------------------------------------------
# Section 2: Conversational Follow-ups
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 💬 Conversation & Follow-up Assistant")
st.caption(
    "Ask questions about your observations, such as: "
    "*'What did you notice in my previous photo?'*, *'What did I mention last time?'*, "
    "or *'What differences did I describe between these observations?'*"
)

# Display Chat History
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("image") is not None:
                st.image(msg["image"], width=220, caption="Attached observation photo")
            st.markdown(msg["content"])
            if "timestamp" in msg:
                st.caption(f"🕒 {msg['timestamp']}")

# Follow-up Chat Input
followup_input = st.chat_input("Ask a follow-up question about your observations...")
if followup_input:
    if not followup_input.strip():
        st.warning("Please type a question before sending.")
    elif not api_key or st.session_state.chat is None:
        st.error("Gemini AI is not connected. Please provide an API key in the sidebar.")
    else:
        # Add user message to conversation
        st.session_state.messages.append(
            {
                "role": "user",
                "content": followup_input.strip(),
                "image": None,
                "timestamp": datetime.now().strftime("%I:%M %p"),
            }
        )

        with st.spinner("AI is reviewing context and responding..."):
            try:
                # Send to Gemini chat session
                response = send_chat_message_with_retry(st.session_state.chat, followup_input.strip())
                ai_text = response.text

                # Append assistant message
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": ai_text,
                        "image": None,
                        "timestamp": datetime.now().strftime("%I:%M %p"),
                    }
                )
                st.rerun()
            except Exception as e:
                display_gemini_error(e, api_key)

# -----------------------------------------------------------------------------
# Section 3: Observation Timeline
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 📈 Chronological Observation Timeline")
st.write("Chronological log of all visible observations recorded during this session.")

if not st.session_state.observations:
    st.info("No observations recorded yet. Use the **Observation Assistant** above to add your first photo or note.")
else:
    for idx, obs in enumerate(st.session_state.observations, start=1):
        with st.container():
            st.markdown(
                f"""
                <div class="timeline-card">
                    <span class="timeline-badge">Observation #{idx} • {obs['timestamp']}</span>
                """,
                unsafe_allow_html=True,
            )

            col_img, col_desc = st.columns([1, 2])

            with col_img:
                if obs["image"] is not None:
                    st.image(obs["image"], caption=f"Observation #{idx} Photo", use_container_width=True)
                else:
                    st.caption("📷 *No photo attached with this entry*")

            with col_desc:
                st.markdown(f"**✍️ User Note:**\n{obs['user_note']}")
                st.markdown(f"**🤖 AI Visible Observation:**\n{obs['ai_observation']}")

            st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Section 4: Observation Summary & WhatsApp Sharing
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 📋 Observation Summary & WhatsApp Export")
st.write("Generate a structured summary of all observations from this session to share with your healthcare provider.")

col_sum_btn, col_sum_status = st.columns([1, 2])

with col_sum_btn:
    generate_summary_clicked = st.button(
        "Generate Observation Summary",
        type="primary",
        use_container_width=True,
        help="Summarize all session observations and discussion for doctor review.",
    )

if generate_summary_clicked:
    if not st.session_state.observations and len(st.session_state.messages) <= 1:
        st.warning("Please record at least one observation before generating a summary.")
    elif not api_key or st.session_state.chat is None:
        st.error("Gemini AI is not connected. Please provide an API key in the sidebar.")
    else:
        with st.spinner("Generating clinical observation summary with Gemini AI..."):
            try:
                # Prepare context summary request
                summary_prompt = (
                    f"{SUMMARY_REQUEST_PROMPT}\n\n"
                    f"Patient / Caregiver Name: {st.session_state.name}\n"
                    f"Total Observations Recorded: {len(st.session_state.observations)}\n\n"
                    f"Please review the conversation and chronological observations recorded above "
                    f"and output a comprehensive, structured summary according to instructions."
                )
                response = send_chat_message_with_retry(st.session_state.chat, summary_prompt)
                st.session_state.summary_text = response.text
                st.success("✅ Summary generated successfully!")
                st.rerun()
            except Exception as e:
                display_gemini_error(e, api_key)

# Display Summary if Generated
if st.session_state.summary_text:
    st.markdown('<div class="summary-card">', unsafe_allow_html=True)
    st.markdown("#### 📄 Clinical Observation Summary")
    st.markdown(st.session_state.summary_text)
    st.markdown("</div>", unsafe_allow_html=True)

    # WhatsApp Sharing Controls
    st.markdown("#### 📲 Send Summary to WhatsApp")
    st.write(
        f"Send this summary to **{st.session_state.name}** at `whatsapp:{st.session_state.whatsapp_number}` via Twilio."
    )

    wa_col1, wa_col2 = st.columns([1, 2])
    with wa_col1:
        send_wa_clicked = st.button("Send Summary to WhatsApp", use_container_width=True)

    if send_wa_clicked:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            st.info(
                "ℹ️ **Twilio WhatsApp is in local testing mode.**\n\n"
                "To send actual WhatsApp messages via Twilio, add your Twilio credentials to `.streamlit/secrets.toml`:\n"
                "```toml\n"
                "TWILIO_ACCOUNT_SID = \"AC...\"\n"
                "TWILIO_AUTH_TOKEN = \"your-auth-token\"\n"
                "TWILIO_WHATSAPP_FROM = \"whatsapp:+14155238886\"\n"
                "TWILIO_CONTENT_SID = \"HX...\"  # (Optional)\n"
                "```\n"
                "You can still copy or download the summary below!"
            )
        else:
            with st.spinner("Sending message through Twilio WhatsApp..."):
                success, msg_info = send_whatsapp_summary(
                    to_number=st.session_state.whatsapp_number,
                    user_name=st.session_state.name,
                    summary_text=st.session_state.summary_text,
                )
                if success:
                    st.success(f"✅ {msg_info}")
                else:
                    st.error(f"❌ {msg_info}")

    # Direct WhatsApp Sharing Link & Download Options
    import urllib.parse

    clean_dest_phone = (
        st.session_state.whatsapp_number.replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )
    wa_message_text = (
        f"🩺 *Health Observation Tracker Summary*\n\n"
        f"👤 *Patient / Caregiver:* {st.session_state.name}\n"
        f"📅 *Generated:* {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n\n"
        f"{st.session_state.summary_text}\n\n"
        f"---\n"
        f"⚠️ *Notice:* This summary records visible observations for discussion with your healthcare professional and is not a medical diagnosis."
    )
    encoded_wa_msg = urllib.parse.quote(wa_message_text)
    wa_direct_url = f"https://wa.me/{clean_dest_phone}?text={encoded_wa_msg}"

    st.markdown("---")
    st.markdown("##### 📤 Direct Export & Sharing Options")
    share_col1, share_col2 = st.columns([1, 1])
    with share_col1:
        st.link_button(
            "📲 Open & Send in WhatsApp (Free)",
            wa_direct_url,
            help="Opens WhatsApp Web or mobile app with your summary pre-filled to your number, no Twilio subscription needed!",
            use_container_width=True,
        )
    with share_col2:
        st.download_button(
            label="📥 Download Summary as Markdown",
            data=st.session_state.summary_text,
            file_name=f"health_observation_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
