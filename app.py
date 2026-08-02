import streamlit as st
from streamlit_oauth import OAuth2Component
from groq import Groq
import os

# Page Configuration
st.set_page_config(page_title="AI Subtitle Studio", page_icon="🎬", layout="wide")

# Read Secrets
CLIENT_ID = st.secrets["google_oauth"]["client_id"]
CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
REDIRECT_URI = st.secrets["google_oauth"]["redirect_uri"]

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_TOKEN_URL = "https://oauth2.googleapis.com/revoke"

# Initialize OAuth Component
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_TOKEN_URL)

# Check User Authentication State
if "token" not in st.session_state:
    st.title("🔒 AI Subtitle Studio - Access Restricted")
    st.write("Please sign in with your Google Account to access the dashboard.")
    
    result = oauth2.authorize_button(
        name="Continue with Google",
        icon="https://www.google.com/favicon.ico",
        redirect_uri=REDIRECT_URI,
        scope="openid email profile",
        key="google_auth",
    )
    
    if result and "token" in result:
        st.session_state["token"] = result["token"]
        st.rerun()

else:
    # Authenticated Interface
    st.sidebar.button("Log Out", on_click=lambda: st.session_state.clear())
    st.title("🎬 AI Subtitle Studio Dashboard")
    st.success("Successfully Authenticated!")
    
    # File Uploader & Processing logic goes here
    uploaded_file = st.file_uploader("Upload Audio/Video", type=["mp4", "mp3", "wav", "m4a"])
    if uploaded_file:
        st.info("File uploaded! Ready for transcription with Whisper-large-v3.")
