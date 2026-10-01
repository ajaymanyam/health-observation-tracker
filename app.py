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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Clean Modern Healthcare SaaS Theme Tokens */
    :root {
        --primary: #0F766E;
        --primary-hover: #0D635C;
        --primary-active: #0B4F4A;
        --primary-dark: #123B63;
        --bg-main: #F8FAFC;
        --bg-sidebar: #F1F5F9;
        --bg-info: #EFF6FF;
        --text-main: #1E293B;
        --text-secondary: #64748B;
        --border-color: #D9E2EC;
        --card-bg: #FFFFFF;
    }

    /* Overall Layout & Typography */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        color: #1E293B;
        background-color: #F8FAFC !important;
    }

    .block-container {
        max-width: 1040px !important;
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
        border-right: 1px solid #D9E2EC !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: #F1F5F9 !important;
        padding: 1.5rem 1.25rem 2rem 1.25rem !important;
    }
    .sidebar-brand {
        margin-bottom: 1.25rem;
        padding-bottom: 0.85rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .sidebar-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #123B63;
        margin: 0;
        letter-spacing: -0.015em;
        line-height: 1.3;
    }
    .sidebar-subtitle {
        font-size: 0.82rem;
        color: #64748B;
        margin: 0.25rem 0 0 0;
        line-height: 1.35;
    }

    /* System Status Component */
    .status-card {
        background-color: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.85rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }
    .status-card-header {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #123B63;
        margin-bottom: 0.5rem;
    }
    .status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.4rem 0;
        font-size: 0.86rem;
        color: #1E293B;
    }
    .status-row:not(:last-child) {
        border-bottom: 1px solid #F1F5F9;
    }
    .status-label {
        font-weight: 500;
        color: #1E293B;
    }
    .status-pill-green {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background-color: #DCFCE7;
        color: #166534;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        letter-spacing: 0.01em;
    }
    .status-dot-green {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #16A34A;
        display: inline-block;
    }
    .status-pill-gray {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background-color: #F1F5F9;
        color: #64748B;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
    }
    .status-dot-gray {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #94A3B8;
        display: inline-block;
    }

    /* Privacy Information Card */
    .privacy-card {
        background-color: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }
    .privacy-card-title {
        font-size: 0.84rem;
        font-weight: 700;
        color: #123B63;
        margin-bottom: 0.3rem;
    }
    .privacy-card-text {
        font-size: 0.8rem;
        color: #64748B;
        line-height: 1.4;
        margin: 0;
    }

    /* Main Header */
    .main-header-wrapper {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1.75rem;
        padding-bottom: 1.25rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #123B63;
        letter-spacing: -0.025em;
        margin: 0 0 0.35rem 0;
        line-height: 1.2;
    }
    .main-subtitle {
        font-size: 1.02rem;
        color: #64748B;
        margin: 0;
        line-height: 1.5;
    }
    .header-accent {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background-color: #EFF6FF;
        color: #0F766E;
        border: 1px solid #BFDBFE;
        padding: 0.4rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
        margin-top: 0.25rem;
    }
    .header-accent-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #0F766E;
        display: inline-block;
    }

    /* Safety / Information Card */
    .safety-card {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-left: 4px solid #2563EB;
        border-radius: 10px;
        padding: 1.15rem 1.4rem;
        margin-bottom: 2rem;
        box-shadow: 0 1px 3px rgba(37, 99, 235, 0.04);
        display: flex;
        gap: 0.9rem;
        align-items: flex-start;
    }
    .safety-icon {
        font-size: 1.3rem;
        line-height: 1.3;
        color: #2563EB;
        flex-shrink: 0;
    }
    .safety-title {
        font-size: 0.98rem;
        font-weight: 700;
        color: #123B63;
        margin-bottom: 0.35rem;
    }
    .safety-message {
        font-size: 0.92rem;
        color: #334155;
        line-height: 1.55;
        margin: 0;
    }
    .safety-highlight {
        font-weight: 700;
        color: #1E3A8A;
        background-color: #DBEAFE;
        padding: 1px 6px;
        border-radius: 4px;
    }

    /* Onboarding Card container styling */
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D9E2EC !important;
        border-radius: 14px !important;
        padding: 2.25rem 2rem 2rem 2rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -2px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 2rem !important;
    }
    .onboarding-card-header {
        margin-bottom: 1.5rem;
        padding-bottom: 0.85rem;
        border-bottom: 1px solid #F1F5F9;
    }
    .onboarding-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #123B63;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.015em;
    }
    .onboarding-subtext {
        font-size: 0.95rem;
        color: #64748B;
        margin: 0;
        line-height: 1.45;
    }

    /* Section Headers & Layout */
    .section-divider {
        border: none;
        border-top: 1px solid #E2E8F0;
        margin: 2.5rem 0 2rem 0;
    }
    .section-header {
        margin-bottom: 1.25rem;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #123B63;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.01em;
    }
    .section-subtitle {
        font-size: 0.92rem;
        color: #64748B;
        margin: 0;
        line-height: 1.45;
    }

    /* Timeline Cards */
    .timeline-card {
        background-color: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    .timeline-badge {
        display: inline-block;
        background-color: #EFF6FF;
        color: #123B63;
        border: 1px solid #BFDBFE;
        font-weight: 600;
        font-size: 0.82rem;
        padding: 0.28rem 0.75rem;
        border-radius: 9999px;
        margin-bottom: 0.85rem;
    }

    /* Summary Card */
    .summary-card {
        background-color: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-radius: 12px;
        padding: 1.65rem;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
    }

    /* Primary Teal Button: #0F766E */
    button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button,
    .stButton > button[kind="primary"] {
        background-color: #0F766E !important;
        color: #FFFFFF !important;
        border: 1px solid #0F766E !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.98rem !important;
        padding: 0.68rem 1.6rem !important;
        box-shadow: 0 1px 2px rgba(15, 118, 110, 0.2) !important;
        transition: background-color 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease !important;
        cursor: pointer !important;
    }
    button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover,
    .stButton > button[kind="primary"]:hover {
        background-color: #0D635C !important;
        border-color: #0D635C !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 6px -1px rgba(15, 118, 110, 0.25) !important;
    }
    button[kind="primary"]:active,
    div[data-testid="stFormSubmitButton"] > button:active,
    .stButton > button[kind="primary"]:active {
        background-color: #0B4F4A !important;
        border-color: #0B4F4A !important;
    }

    /* Secondary Button */
    button[kind="secondary"],
    .stButton > button[kind="secondary"],
    div[data-testid="stDownloadButton"] > button,
    a[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #123B63 !important;
        border: 1px solid #D9E2EC !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.55rem 1.25rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.15s ease !important;
    }
    button[kind="secondary"]:hover,
    .stButton > button[kind="secondary"]:hover,
    div[data-testid="stDownloadButton"] > button:hover,
    a[kind="secondary"]:hover {
        background-color: #EFF6FF !important;
        border-color: #0F766E !important;
        color: #0F766E !important;
    }

    /* Inputs & Form Controls */
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: #FFFFFF !important;
        border: 1px solid #D9E2EC !important;
        border-radius: 8px !important;
        color: #1E293B !important;
        font-size: 0.95rem !important;
        padding: 0.65rem 0.85rem !important;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #0F766E !important;
        box-shadow: 0 0 0 2px rgba(15, 118, 110, 0.15) !important;
    }
    label, [data-testid="stWidgetLabel"] label, [data-testid="stWidgetLabel"] p {
        color: #123B63 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        margin-bottom: 0.35rem !important;
    }

    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D9E2EC !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        margin-bottom: 0.85rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    }

    /* Chat Input */
    [data-testid="stChatInput"] {
        border-color: #D9E2EC !important;
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #0F766E !important;
        box-shadow: 0 0 0 2px rgba(15, 118, 110, 0.15) !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D9E2EC !important;
        border-radius: 10px !important;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D9E2EC !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        margin-bottom: 0.5rem !important;
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
    st.markdown(
        """
        <div class="sidebar-brand">
            <h1 class="sidebar-title">🩺 Health Tracker</h1>
            <p class="sidebar-subtitle">Observation Documentation Assistant</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    # System Status Section
    st.markdown('<div class="status-card-header">System Status</div>', unsafe_allow_html=True)

    gemini_pill = (
        '<span class="status-pill-green"><span class="status-dot-green"></span>Connected</span>'
        if eff_key else
        '<span class="status-pill-gray"><span class="status-dot-gray"></span>API Key Needed</span>'
    )
    twilio_pill = (
        '<span class="status-pill-green"><span class="status-dot-green"></span>Configured</span>'
        if (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN) else
        '<span class="status-pill-gray"><span class="status-dot-gray"></span>Local Test Mode</span>'
    )

    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-row">
                <span class="status-label">Gemini AI</span>
                {gemini_pill}
            </div>
            <div class="status-row">
                <span class="status-label">Twilio WhatsApp</span>
                {twilio_pill}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Privacy Information Card
    st.markdown(
        """
        <div class="privacy-card">
            <div class="privacy-card-title">🔒 Your Privacy</div>
            <p class="privacy-card-text">Your information is used only for this session.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    st.markdown(
        """
        <div class="main-header-wrapper">
            <div>
                <h1 class="main-title">🩺 Health Observation Tracker</h1>
                <p class="main-subtitle">Record, organize, and review visible health observations over time with multimodal AI.</p>
            </div>
            <div class="header-accent">
                <span class="header-accent-dot"></span> Clinical Documentation Aid
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="safety-card">
            <div class="safety-icon">ℹ️</div>
            <div>
                <div class="safety-title">Documentation & Communication Assistant</div>
                <p class="safety-message">
                    This application is designed solely to help patients and caregivers objectively document visible health observations 
                    and communicate clearly with healthcare providers. It <span class="safety-highlight">does not diagnose</span> medical 
                    conditions, prescribe medications, or replace professional medical care.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("onboarding_form", clear_on_submit=False):
        st.markdown(
            """
            <div class="onboarding-card-header">
                <h2 class="onboarding-title">👋 Welcome! Let's get started.</h2>
                <p class="onboarding-subtext">Please provide your name and WhatsApp number to begin your session.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            name_input = st.text_input(
                "👤 Patient / Caregiver Name *",
                placeholder="e.g., Jane Doe",
                help="The name used to personalize your observation records.",
            )
        with col2:
            phone_input = st.text_input(
                "📱 WhatsApp Number *",
                placeholder="e.g., +1 555 123 4567",
                help="Include country code (e.g. +1 for US, +44 for UK, +91 for India).",
            )

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
        submit_onboarding = st.form_submit_button("Start Tracking Observations", type="primary", use_container_width=True)

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
st.markdown(
    f"""
    <div class="main-header-wrapper">
        <div>
            <h1 class="main-title">🩺 Health Observation Tracker</h1>
            <p class="main-subtitle">Active Session for <strong style="color: #123B63;">{st.session_state.name}</strong> • WhatsApp: <code style="color: #0F766E; background: #EFF6FF; padding: 2px 7px; border-radius: 4px; font-weight: 600;">{st.session_state.whatsapp_number}</code></p>
        </div>
        <div class="header-accent">
            <span class="header-accent-dot"></span> Clinical Documentation Aid
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Safety notice banner
st.markdown(
    """
    <div class="safety-card">
        <div class="safety-icon">🛡️</div>
        <div>
            <div class="safety-title">Safe Health Tracking Notice</div>
            <p class="safety-message">
                All AI descriptions describe visible characteristics only. The assistant <span class="safety-highlight">does not make diagnoses</span> 
                or recommend treatments. If you experience severe symptoms or discomfort, please consult a qualified healthcare professional promptly.
            </p>
        </div>
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
st.markdown(
    """
    <div class="section-header">
        <h2 class="section-title">📸 Observation Assistant</h2>
        <p class="section-subtitle">Record a new visible health observation. You may provide a photo, written notes, or both.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="section-header">
        <h2 class="section-title">💬 Conversation & Follow-up Assistant</h2>
        <p class="section-subtitle">Ask questions about your observations, review visible changes over time, or clarify notes.</p>
    </div>
    """,
    unsafe_allow_html=True,
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
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="section-header">
        <h2 class="section-title">📈 Chronological Observation Timeline</h2>
        <p class="section-subtitle">Chronological record of all visible health observations documented during this session.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="section-header">
        <h2 class="section-title">📋 Observation Summary & WhatsApp Export</h2>
        <p class="section-subtitle">Generate a structured clinical summary of all observations from this session to share with your healthcare provider.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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
