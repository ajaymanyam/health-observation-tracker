# 📋 To-Do & Configuration Guide: API Keys & Credentials

This guide provides a step-by-step checklist on **how to get each API key/credential** and **where to insert them** for the **Health Observation Tracker**.

---

## 🎯 Quick Overview

| Credential | Service | Required? | Purpose |
| :--- | :--- | :---: | :--- |
| `GEMINI_API_KEY` | Google AI Studio | **Yes** | AI visual analysis, conversation & summary |
| `TWILIO_ACCOUNT_SID` | Twilio Console | *Optional* | Sending observation summary to WhatsApp |
| `TWILIO_AUTH_TOKEN` | Twilio Console | *Optional* | Authenticating WhatsApp messages |
| `TWILIO_WHATSAPP_FROM` | Twilio Sandbox | *Optional* | The Twilio WhatsApp sender number |
| `TWILIO_CONTENT_SID` | Twilio Content API | *Optional* | Approved WhatsApp Content Template |

> 💡 **Note:** If you do not have Twilio credentials yet, the entire application still works in **Local Test Mode**! You can record observations, chat with Gemini, generate summaries, and download or copy them.

---

## 📝 Step-by-Step To-Do Checklist

### Part 1: Where to Insert the Keys

- [ ] **1. Create the secrets file**
  In your project folder, create a new file named `.streamlit/secrets.toml`:
  * Path: `c:\Users\HP\OneDrive\Desktop\med\.streamlit\secrets.toml`
  *(You can duplicate `secrets.toml.example` and rename it to `secrets.toml`)*

- [ ] **2. Copy the template into `secrets.toml`**:
  ```toml
  GEMINI_API_KEY = "your-gemini-api-key-here"

  TWILIO_ACCOUNT_SID = "your-twilio-account-sid-here"
  TWILIO_AUTH_TOKEN = "your-twilio-auth-token-here"

  TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"

  TWILIO_CONTENT_SID = "your-content-template-sid-here"
  ```

---

### Part 2: How to Get Your Keys

#### 🔑 A. Google Gemini API Key (`GEMINI_API_KEY`)
- [ ] Go to [Google AI Studio](https://aistudio.google.com/).
- [ ] Sign in with your Google account.
- [ ] Click **Get API key** in the left sidebar.
- [ ] Click **Create API key** (choose an existing Google Cloud project or create a new one).
- [ ] Copy the generated API key (it starts with `AIzaSy...`).
- [ ] Paste it into `.streamlit/secrets.toml`:
  ```toml
  GEMINI_API_KEY = "AIzaSy..."
  ```
  *(Alternative: You can also paste it directly into the app's sidebar in your browser).*

---

#### 📲 B. Twilio Account SID & Auth Token (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`)
*(Only needed if you want to send summaries directly to WhatsApp)*

- [ ] Sign up or log in at [Twilio](https://www.twilio.com/).
- [ ] Navigate to the [Twilio Console Dashboard](https://console.twilio.com/).
- [ ] Under the **Account Info** section on the main page, find:
  - **Account SID** (starts with `AC...`)
  - **Auth Token** (click "Show" to reveal)
- [ ] Copy and paste them into `.streamlit/secrets.toml`:
  ```toml
  TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  TWILIO_AUTH_TOKEN = "your_auth_token_here"
  ```

---

#### 💬 C. Twilio WhatsApp Sender (`TWILIO_WHATSAPP_FROM`)
*(For testing with Twilio WhatsApp Sandbox)*

- [ ] In the Twilio Console, go to **Messaging** > **Try it out** > **Send a WhatsApp message**.
- [ ] You will see your sandbox number, typically:
  ```text
  whatsapp:+14155238886
  ```
- [ ] Follow Twilio's instructions on that page to join the sandbox from your personal phone (e.g., send `join <your-sandbox-keyword>` to the sandbox number on WhatsApp).
- [ ] Add the number to `.streamlit/secrets.toml`:
  ```toml
  TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
  ```

---

#### 📄 D. Twilio Content Template SID (`TWILIO_CONTENT_SID`) *(Optional)*
- [ ] If you have created a WhatsApp Content Template under **Messaging** > **Content Template Builder**, copy its Template SID (starts with `HX...`).
- [ ] Paste it into `.streamlit/secrets.toml`:
  ```toml
  TWILIO_CONTENT_SID = "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  ```
- [ ] *If you don't have a Content Template, leave this blank or omitted; the app automatically falls back to standard WhatsApp direct messages.*

---

### Part 3: Deploying to Streamlit Community Cloud

When you deploy to Streamlit Cloud:

- [ ] Push your repository to GitHub (ensure `.streamlit/secrets.toml` is **not** committed; `.gitignore` already protects it).
- [ ] Go to your app dashboard on [Streamlit Community Cloud](https://share.streamlit.io/).
- [ ] Click **App Settings** (three dots next to your app) > **Secrets**.
- [ ] Paste your TOML block:
  ```toml
  GEMINI_API_KEY = "AIzaSy..."
  TWILIO_ACCOUNT_SID = "AC..."
  TWILIO_AUTH_TOKEN = "..."
  TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
  TWILIO_CONTENT_SID = "HX..."
  ```
- [ ] Click **Save**. The app will automatically reload with your live credentials!
