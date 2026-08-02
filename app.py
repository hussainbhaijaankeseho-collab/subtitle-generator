import streamlit as st
from streamlit_oauth import OAuth2Component
from groq import Groq
import os
import time

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM STYLING (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Subtitle Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern dark UI, glassmorphism, and custom buttons
st.markdown("""
<style>
    /* Global Container Padding & Colors */
    .stApp {
        background-color: #0e1117;
        color: #e0e6ed;
    }
    
    /* Modern Card Container */
    .css-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    
    /* Sleek Title Styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5, #9333EA, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #9CA3AF;
        margin-bottom: 25px;
    }

    /* Metric Box Customization */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700;
        color: #6366F1;
    }
    
    /* Streamlit Button Overrides */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. OAUTH 2.0 CONFIGURATION
# -----------------------------------------------------------------------------
CLIENT_ID = st.secrets["google_oauth"]["client_id"]
CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
REDIRECT_URI = st.secrets["google_oauth"]["redirect_uri"]

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_TOKEN_URL = "https://oauth2.googleapis.com/revoke"

oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_TOKEN_URL)

# -----------------------------------------------------------------------------
# 3. AUTHENTICATION GATE
# -----------------------------------------------------------------------------
if "token" not in st.session_state:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="css-card" style="text-align: center;">
            <h1 class="main-title">🔒 AI Subtitle Studio</h1>
            <p class="sub-title">High-performance automated subtitle generation powered by Groq & Whisper v3</p>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 20px 0;">
            <p style="color: #D1D5DB;">Sign in to unlock full workspace capabilities.</p>
        </div>
        """, unsafe_allow_html=True)
        
        result = oauth2.authorize_button(
            name="Continue with Google",
            icon="https://www.google.com/favicon.ico",
            redirect_uri=REDIRECT_URI,
            scope="openid email profile",
            key="google_auth",
            use_container_width=True
        )
        
        if result and "token" in result:
            st.session_state["token"] = result["token"]
            st.rerun()

# -----------------------------------------------------------------------------
# 4. DASHBOARD (AUTHENTICATED USER INTERFACE)
# -----------------------------------------------------------------------------
else:
    # Sidebar Setup
    with st.sidebar:
        st.markdown("### 👤 User Workspace")
        st.markdown('<span class="status-badge">● Google Authenticated</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("⚙️ Settings")
        language_option = st.selectbox("Target Language", ["Auto-Detect", "English", "Spanish", "French", "German", "Urdu", "Japanese"])
        export_format = st.radio("Subtitle Export Format", ["SubRip (.srt)", "WebVTT (.vtt)", "Plain Text (.txt)"])
        
        st.markdown("---")
        if st.button("Log Out", use_container_width=True, type="secondary"):
            st.session_state.clear()
            st.rerun()

    # Main Header Section
    st.markdown('<h1 class="main-title">🎬 AI Subtitle Studio</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Generate ultra-fast subtitles using Groq Whisper-Large-V3</p>', unsafe_allow_html=True)

    # Top Analytics / Info Cards
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="AI Model", value="Whisper v3", delta="Groq Accelerated")
    with m2:
        st.metric(label="Audio Engine", value="FFmpeg", delta="Ready")
    with m3:
        st.metric(label="Processing Speed", value="~100x Real-time", delta="Optimal")

    st.markdown("<br>", unsafe_allow_html=True)

    # File Upload & Processing Workspace
    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown("### 📥 Upload Media File")
        uploaded_file = st.file_uploader(
            "Select an audio or video file", 
            type=["mp4", "mp3", "wav", "m4a", "mov", "mkv"],
            help="Supported formats: MP4, MP3, WAV, M4A, MOV, MKV"
        )
        
        if uploaded_file:
            st.success(f"File **{uploaded_file.name}** uploaded ({round(uploaded_file.size / (1024 * 1024), 2)} MB)")
            
            # Preview player
            if uploaded_file.type.startswith("video"):
                st.video(uploaded_file)
            else:
                st.audio(uploaded_file)
                
            generate_btn = st.button("🚀 Transcribe & Generate Subtitles", type="primary", use_container_width=True)

    with right_col:
        st.markdown("### 📝 Subtitle Output")
        
        if uploaded_file and 'generate_btn' in locals() and generate_btn:
            with st.spinner("⚡ Extracting audio & running Whisper-large-v3 model..."):
                # Simulation placeholder for API Call / FFmpeg processing
                time.sleep(2) 
                
                # Mocked output for display preview
                sample_srt = """1
00:00:01,000 --> 00:00:04,500
Welcome to AI Subtitle Studio!

2
00:00:04,800 --> 00:00:08,200
Your media file was transcribed successfully using Groq acceleration.
"""
                st.markdown("#### Preview:")
                st.text_area("Generated Output", sample_srt, height=250)
                
                st.download_button(
                    label="📥 Download Subtitles",
                    data=sample_srt,
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}.srt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("Upload a file on the left and click **Transcribe** to see real-time subtitles here.")
