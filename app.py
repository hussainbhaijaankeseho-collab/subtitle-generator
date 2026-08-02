import streamlit as st
from streamlit_oauth import OAuth2Component
from groq import Groq
import os
import tempfile
import datetime

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Subtitle Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e6ed; }
    .css-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5, #9333EA, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title { font-size: 1rem; color: #9CA3AF; margin-bottom: 25px; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700; color: #6366F1; }
    .stButton>button { border-radius: 8px; font-weight: 600; transition: all 0.2s ease; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3); }
    .status-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.85rem; font-weight: 600; background: rgba(16, 185, 129, 0.15);
        color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. HELPER FUNCTIONS FOR SRT & TRANSLATION
# -----------------------------------------------------------------------------
def format_timestamp(seconds: float) -> str:
    """Converts seconds into SRT timestamp format 00:00:00,000"""
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millisecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def translate_text(groq_client, text: str, target_lang: str) -> str:
    """Translates a single subtitle line using Groq's Llama-3 model."""
    if target_lang == "Original Audio Language":
        return text
        
    prompt = f"Translate the following subtitle text to {target_lang}. Return ONLY the direct translation, preserving original tone and brevity without extra quotes or conversational response:\n\n{text}"
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# -----------------------------------------------------------------------------
# 3. OAUTH 2.0 CONFIGURATION
# -----------------------------------------------------------------------------
CLIENT_ID = st.secrets["google_oauth"]["client_id"]
CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
REDIRECT_URI = st.secrets["google_oauth"]["redirect_uri"]
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_TOKEN_URL = "https://oauth2.googleapis.com/revoke"

oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_TOKEN_URL)

# -----------------------------------------------------------------------------
# 4. AUTHENTICATION GATE
# -----------------------------------------------------------------------------
if "token" not in st.session_state:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="css-card" style="text-align: center;">
            <h1 class="main-title">🔒 AI Subtitle Studio</h1>
            <p class="sub-title">High-performance automated subtitle generation powered by Groq & Whisper v3</p>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 20px 0;">
            <p style="color: #D1D5DB;">Sign in with Google to access your dashboard.</p>
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
# 5. DASHBOARD
# -----------------------------------------------------------------------------
else:
    with st.sidebar:
        st.markdown("### 👤 User Workspace")
        st.markdown('<span class="status-badge">● Google Authenticated</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("⚙️ Output Settings")
        export_format = st.radio("Subtitle Format", ["SubRip (.srt)", "Plain Text (.txt)"])
        
        st.markdown("---")
        if st.button("Log Out", use_container_width=True, type="secondary"):
            st.session_state.clear()
            st.rerun()

    st.markdown('<h1 class="main-title">🎬 AI Subtitle Studio</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Transcribe & Translate Subtitles into Any Language using Groq</p>', unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Transcription Model", value="Whisper v3", delta="Groq")
    with m2:
        st.metric(label="Translation Engine", value="Llama 3.3", delta="Groq")
    with m3:
        st.metric(label="Processing Speed", value="Ultra-Fast", delta="Optimal")

    st.markdown("<br>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown("### 🌐 Target Subtitle Language")
        
        target_languages = [
            "Original Audio Language",
            "English",
            "Urdu",
            "Spanish",
            "French",
            "German",
            "Japanese",
            "Chinese",
            "Arabic",
            "Hindi"
        ]
        
        selected_target_lang = st.selectbox(
            "Select Desired Output Subtitle Language", 
            target_languages,
            help="Subtitles will be automatically translated into this language."
        )

        uploaded_file = st.file_uploader(
            "Upload Audio or Video File", 
            type=["mp4", "mp3", "wav", "m4a", "mov", "mkv"]
        )
        
        if uploaded_file:
            st.success(f"File **{uploaded_file.name}** uploaded ({round(uploaded_file.size / (1024 * 1024), 2)} MB)")
            if uploaded_file.type.startswith("video"):
                st.video(uploaded_file)
            else:
                st.audio(uploaded_file)
                
            generate_btn = st.button("🚀 Transcribe & Generate Subtitles", type="primary", use_container_width=True)

    with right_col:
        st.markdown("### 📝 Subtitle Output")
        
        if uploaded_file and 'generate_btn' in locals() and generate_btn:
            if not GROQ_API_KEY:
                st.error("Missing `GROQ_API_KEY` in Streamlit Secrets!")
            else:
                groq_client = Groq(api_key=GROQ_API_KEY)
                
                with st.spinner("⚡ Step 1: Transcribing audio with Whisper-large-v3..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = tmp_file.name

                    try:
                        with open(tmp_path, "rb") as audio_file:
                            transcript = groq_client.audio.transcriptions.create(
                                file=(uploaded_file.name, audio_file.read()),
                                model="whisper-large-v3",
                                response_format="verbose_json"
                            )
                        
                        segments = transcript.segments if hasattr(transcript, 'segments') else transcript.get('segments', [])
                        
                        srt_output = []
                        txt_output = []
                        
                        progress_bar = st.progress(0, text="Translating subtitles...")
                        total_segments = len(segments)
                        
                        for idx, segment in enumerate(segments):
                            start_time = format_timestamp(segment.get('start', 0) if isinstance(segment, dict) else segment.start)
                            end_time = format_timestamp(segment.get('end', 0) if isinstance(segment, dict) else segment.end)
                            raw_text = (segment.get('text', '') if isinstance(segment, dict) else segment.text).strip()
                            
                            # Translate line if multi-language selected
                            final_text = translate_text(groq_client, raw_text, selected_target_lang)
                            
                            # Build SRT block
                            srt_entry = f"{idx + 1}\n{start_time} --> {end_time}\n{final_text}\n"
                            srt_output.append(srt_entry)
                            txt_output.append(final_text)
                            
                            if total_segments > 0:
                                progress_bar.progress((idx + 1) / total_segments, text=f"Translating segment {idx+1}/{total_segments}...")
                        
                        progress_bar.empty()
                        
                        final_subtitles = "\n".join(srt_output) if "SubRip" in export_format else "\n".join(txt_output)
                        
                        st.markdown(f"#### Generated Subtitles ({selected_target_lang}):")
                        st.text_area("Result Preview", final_subtitles, height=280)
                        
                        file_ext = ".srt" if "SubRip" in export_format else ".txt"
                        st.download_button(
                            label="📥 Download Subtitles",
                            data=final_subtitles,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{selected_target_lang}{file_ext}",
                            mime="text/plain",
                            use_container_width=True
                        )

                    except Exception as e:
                        st.error(f"Error processing audio: {str(e)}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
        else:
            st.info("Upload a file, choose your target subtitle language, and click **Transcribe**.")
