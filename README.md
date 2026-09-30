# 🩺 Health Observation Tracker

A web application built with Streamlit, Google Gemini (`google-genai`), and Twilio WhatsApp to help patients and caregivers systematically record, track, and organize visible health observations over time.

---

## 🌟 Features

1. **User Onboarding**: Simple onboarding capturing patient/caregiver name and WhatsApp number.
2. **Multimodal Observation Input**: Upload observation photos (JPG, JPEG, PNG) and/or write notes describing visible symptoms, location, and timeline.
3. **AI Observation Assistant**:
   - Analyzes visible visual characteristics (color, margins, texture, swelling, size comparison).
   - Uses neutral, objective language and communicates uncertainty clearly.
   - Strictly bounded: **does not diagnose diseases, recommend medications, or replace medical care**.
4. **Conversational Follow-ups**: Ask questions about previous observations (e.g. *"What did you notice in my previous photo?"*, *"What differences were described?"*), with full conversational context maintained.
5. **Chronological Observation Timeline**: Clean, structured timeline displaying timestamped photos, user notes, and AI observations.
6. **Observation Summary**: Generate a concise, doctor-ready clinical observation summary.
7. **WhatsApp Export via Twilio**: Send the generated summary directly to the patient's WhatsApp number using Twilio Content Templates (with automatic fallback to standard WhatsApp body).
8. **Local Testing Resilience**: Fully testable locally even if Twilio credentials are not yet configured.

---

## 📁 Project Structure

```text
health_observation_tracker/
├── app.py                      # Main Streamlit application
├── prompts.py                  # Gemini AI prompts (System, Welcome, Summary)
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules protecting secrets
└── .streamlit/
    └── secrets.toml.example    # Template for API keys and Twilio credentials
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+ installed
- Google Gemini API key
- (Optional) Twilio Account SID, Auth Token, and WhatsApp sender

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Secrets
Create `.streamlit/secrets.toml` based on `.streamlit/secrets.toml.example`:

```toml
GEMINI_API_KEY = "your-gemini-api-key-here"

TWILIO_ACCOUNT_SID = "your-twilio-account-sid-here"
TWILIO_AUTH_TOKEN = "your-twilio-auth-token-here"

TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"

TWILIO_CONTENT_SID = "your-content-template-sid-here"
```

> **Note:** If `GEMINI_API_KEY` is not placed in `secrets.toml`, you can also enter it directly into the secure key field in the application's sidebar.

### 4. Run the Application
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

---

## ☁️ Deployment on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and create a new app pointing to your repository.
3. Set the Main file path to `app.py`.
4. Under **Advanced settings > Secrets**, paste the keys from `.streamlit/secrets.toml.example` with your real credentials.
5. Click **Deploy!**
# health-observation-tracker
