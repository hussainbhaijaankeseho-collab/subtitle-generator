import streamlit as st
from groq import Groq
import os
import tempfile
import datetime
import subprocess

# Page Configuration
st.set_page_config(
    page_title="AI Subtitle Studio Pro", 
    page_icon="🎬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Dark Theme & Glassmorphism Styling
CUSTOM_CSS = """
<style>
    /* App Background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Title Styling */
    h1 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Subheaders */
    h3, .stSubheader {
        color: #E0E0E0 !important;
        font-weight: 600 !important;
    }

    /* Glassmorphic Cards & Containers */
    div[data-testid="stVerticalBlock"] > div[style*="flex"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Primary Red Gradient Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #FF4B4B 0%, #B30000 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(255, 75, 75, 0.4) !important;
    }

    /* Text Area / Code Box Output Styling */
    textarea {
        background-color: #161B22 !important;
        color: #00FFCC !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        font-family: 'Fira Code', 'Courier New', monospace !important;
        font-size: 0.9rem !important;
    }

    /* File Uploader Container */
    div[data-testid="stFileUploader"] {
        background-color: #161B22;
        border: 1px stroke #30363D;
        border-radius: 10px;
        padding: 10px;
    }

    /* Selectbox Input Styling */
    div[data-baseweb="select"] > div {
        background-color: #161B22 !important;
        border-color: #30363D !important;
        color: #FAFAFA !important;
        border-radius: 8px !important;
    }

    /* Dark Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid #30363D !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------
# 1. Google Account Authentication Gate
# ----------------------------------------------------
if not st.user.is_logged_in:
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🔐 AI Subtitle Studio Pro")
        st.caption("Secure Authentication")
        st.write("Sign in with your Google account to access audio extraction, transcription, and translation tools.")
        st.button("🔑 Log in with Google Account", on_click=st.login, type="primary", use_container_width=True)
    st.stop()

# User Sidebar Section
st.sidebar.title("👤 User Profile")
st.sidebar.markdown(f"Logged in as:\n**{st.user.name}**")
st.sidebar.caption(f"Email: {st.user.email}")
st.sidebar.markdown("---")
st.sidebar.button("🚪 Log Out", on_click=st.logout, use_container_width=True)

# ----------------------------------------------------
# 2. Processing Helpers
# ----------------------------------------------------
def format_timestamp(seconds: float) -> str:
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def extract_audio(input_file_path: str) -> str:
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_audio_path = temp_audio.name
    temp_audio.close()

    cmd = [
        "ffmpeg", "-y", "-i", input_file_path,
        "-vn", "-acodec", "libmp3lame",
        "-ar", "16000", "-ac", "1", "-q:a", "2",
        temp_audio_path
    ]
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        raise Exception(f"FFmpeg extraction failed: {process.stderr.decode('utf-8')}")
    return temp_audio_path

def translate_text(client: Groq, text: str, target_language: str) -> str:
    if target_language.lower() == "english":
        return text

    prompt = (
        f"Translate the following subtitle text to {target_language}. "
        "Maintain tone and context. Return ONLY the translation, no explanation:\n\n"
        f"{text}"
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()

# ----------------------------------------------------
# 3. Main Dashboard Layout
# ----------------------------------------------------
st.title("🎬 AI Subtitle Studio Pro")
st.caption("Powered by FFmpeg, Groq Whisper v3, and Llama 3.3")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("📥 Input & Options")
    target_lang = st.selectbox(
        "Select Target Language",
        ["English", "Spanish", "French", "German", "Japanese", "Chinese", "Arabic", "Hindi", "Urdu"]
    )
    uploaded_file = st.file_uploader(
        "Upload Video or Audio File", 
        type=["mp4", "mp3", "wav", "mkv", "mov", "flac"]
    )
    process_btn = st.button("🚀 Process Media", type="primary", use_container_width=True)

with col_right:
    st.subheader("📝 Subtitle Studio Output")

if process_btn:
    if not uploaded_file:
        st.error("Please upload a media file first!")
    else:
        api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
        if not api_key:
            st.error("GROQ_API_KEY is missing from secrets.")
        else:
            client = Groq(api_key=api_key)
            status = st.empty()
            
            try:
                # Save temp file
                ext = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_input_path = tmp.name

                # 1. Extract Audio
                status.info("⏳ Step 1/3: Extracting audio via FFmpeg...")
                audio_path = extract_audio(tmp_input_path)

                # 2. Transcribe
                status.info("⏳ Step 2/3: Transcribing audio with Groq Whisper v3...")
                with open(audio_path, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), f.read()),
                        model="whisper-large-v3",
                        response_format="verbose_json",
                    )

                # 3. Format & Translate
                status.info("⏳ Step 3/3: Processing subtitles & translation...")
                srt_content = ""
                txt_content = ""
                segments = getattr(transcription, 'segments', [])

                if segments:
                    for idx, seg in enumerate(segments, start=1):
                        start = format_timestamp(seg['start'])
                        end = format_timestamp(seg['end'])
                        text = seg['text'].strip()

                        if target_lang != "English":
                            text = translate_text(client, text, target_lang)

                        srt_content += f"{idx}\n{start} --> {end}\n{text}\n\n"
                        txt_content += f"{text} "
                else:
                    raw_text = transcription.text
                    if target_lang != "English":
                        raw_text = translate_text(client, raw_text, target_lang)
                    txt_content = raw_text
                    srt_content = f"1\n00:00:00,000 --> 00:05:00,000\n{raw_text}\n\n"

                # Cleanup temp files
                if os.path.exists(tmp_input_path):
                    os.remove(tmp_input_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)

                status.empty()

                # Render Results
                with col_right:
                    st.success("✨ Subtitles generated successfully!")
                    st.text_area("SRT Preview", srt_content, height=260)
                    
                    d1, d2 = st.columns(2)
                    with d1:
                        st.download_button(
                            "📥 Download .SRT",
                            srt_content,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}.srt",
                            use_container_width=True
                        )
                    with d2:
                        st.download_button(
                            "📥 Download .TXT",
                            txt_content,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}.txt",
                            use_container_width=True
                        )

            except Exception as e:
                status.empty()
                st.error(f"Error processing file: {e}")
