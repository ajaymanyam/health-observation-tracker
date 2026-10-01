# 🩺 Health Observation Tracker

A modern healthcare SaaS web application built with **Streamlit**, **Google Gemini** multimodal AI (`google-genai`), and **Twilio WhatsApp** to help patients and caregivers systematically document, monitor, and organize visible health observations over time.

---

## 🎨 Modern Healthcare UI Design

The application features a clean, calm, and clinical SaaS design system engineered for clear healthcare documentation:

- **Curated Color System**:
  - **Primary Action**: Healthcare Teal (`#0F766E`) with subtle hover elevation
  - **Navy Branding**: Deep Navy (`#123B63`) for prominent, readable headings
  - **Backgrounds**: Calm Slate (`#F8FAFC`) with soft navigation panels (`#F1F5F9`)
  - **Information & Safety**: Pale Blue (`#EFF6FF`) with `#2563EB` left accent borders
  - **Status Indicators**: Soft green badges (`#DCFCE7` / `#166534`) for active connections
- **Modern Typography**: High-legibility Google Font (*Plus Jakarta Sans*) with clear typographic hierarchy.
- **Card-Based Architecture**: Elevated white cards with subtle borders (`#D9E2EC`) and soft drop-shadows.
- **Responsive Layout**: Balanced desktop and mobile layout with intuitive form controls and side-by-side inputs.

---

## 🌟 Key Features

1. **Patient & Caregiver Onboarding**:
   - Clean, rounded card layout with side-by-side desktop fields for Name and WhatsApp number.
   - Distinct Teal primary action button (`Start Tracking Observations`).

2. **Multimodal Visible Health Observation Recording**:
   - Upload observation photos (`JPG`, `JPEG`, `PNG`) and/or write structured notes describing visible appearance, margins, location, and progression.
   - Gemini multimodal AI analyzes observable characteristics (color, margins, texture, swelling, size comparison).
   - Strictly bounded: **does not diagnose diseases, prescribe medications, or replace medical care**.

3. **Conversational Follow-Up Assistant**:
   - Chat with full session history to compare observations (e.g. *"What differences were described between my photos?"*, *"What should I mention to my physician?"*).

4. **Chronological Observation Timeline**:
   - Visual log of all timestamped photos, user notes, and AI descriptions recorded during the session.

5. **Clinical Observation Summary**:
   - Generate a concise, structured summary designed for review by doctors or healthcare providers.

6. **Flexible Sharing & Export Options**:
   - **Twilio WhatsApp Integration**: Automatically deliver summaries directly to WhatsApp with template and standard fallbacks.
   - **Direct WhatsApp Web / Mobile Link**: 1-click free sharing via `wa.me` without requiring paid Twilio subscriptions.
   - **Markdown Export**: Download full session documentation for personal records or patient portals.

7. **System Status & Session Privacy**:
   - Live status pills for Gemini AI and Twilio WhatsApp connectivity in the sidebar.
   - Privacy-first session scope: observation data is managed strictly in session memory.

---

## 📁 Project Structure

```text
health_observation_tracker/
├── app.py                      # Main Streamlit application with custom SaaS UI
├── prompts.py                  # Gemini AI prompts (System, Welcome, Summary)
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git rules protecting secrets and virtual environments
└── .streamlit/
    ├── config.toml             # Native Streamlit healthcare light theme tokens
    └── secrets.toml.example    # Configuration template for API keys & credentials
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.9+** installed
- **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/))
- *(Optional)* **Twilio Account** credentials for automated WhatsApp messaging

### 2. Installation
Clone the repository and install the dependencies:

```bash
git clone https://github.com/ajaymanyam/health-observation-tracker.git
cd health-observation-tracker
pip install -r requirements.txt
```

### 3. Configure Secrets
Create `.streamlit/secrets.toml` based on `.streamlit/secrets.toml.example`:

```toml
# Google Gemini API Key
GEMINI_API_KEY = "AIzaSy..."

# Twilio WhatsApp Configuration (Optional)
TWILIO_ACCOUNT_SID = "AC..."
TWILIO_AUTH_TOKEN = "your-auth-token"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
TWILIO_CONTENT_SID = "HX..."  # Optional Content Template SID
```

> **Tip:** If you do not have `secrets.toml` set up, you can also enter your Gemini API Key directly into the secure password field in the left sidebar!

### 4. Run the Application
```bash
streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## ☁️ Deployment on Streamlit Community Cloud

1. Push your repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/) and select your repository.
3. Set the Main file path to `app.py`.
4. Under **Advanced settings > Secrets**, paste the keys from `.streamlit/secrets.toml.example` with your real credentials.
5. Click **Deploy!**

---

## ⚠️ Medical Disclaimer

This application is designed solely to help patients and caregivers objectively document visible health observations and communicate clearly with healthcare professionals. It **does not diagnose medical conditions**, prescribe treatments or medications, or replace professional medical advice.
