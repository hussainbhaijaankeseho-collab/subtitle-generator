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

# High-Contrast Bright Dark Theme CSS
CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF !important;
    }
    
    h1, h2, h3, h4, .stHeader {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    label, .stCaption, p, span, div {
        color: #E0E6ED !important;
    }

    div[data-testid="stMetricValue"] > div {
        color: #00FFCC !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }
    div[data-testid="stMetricLabel"] > div {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    div[data-testid="stVerticalBlock"] > div[style*="flex"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 1.5rem;
    }

    .stButton > button {
        background: linear-gradient(135deg, #FF4B4B 0%, #B30000 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(255, 75, 75, 0.4) !important;
    }

    textarea {
        background-color: #161B22 !important;
        color: #00FFCC !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        font-family: 'Fira Code', 'Courier New', monospace !important;
    }

    div[data-testid="stAlert"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #00FFCC !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid #30363D !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------
# 1. Sidebar Platform Info (Google Login Removed)
# ----------------------------------------------------
st.sidebar.title("⚡ Platform Capabilities")
st.sidebar.write("• **Whisper v3**: Ultra-fast transcription")
st.sidebar.write("• **Llama 3.3 70B**: Context-aware translation")
st.sidebar.write("• **FFmpeg Engine**: MP4/MKV/WAV audio conversion")
st.sidebar.markdown("---")
st.sidebar.caption("AI Subtitle Studio Pro is ready for instant media processing.")

# ----------------------------------------------------
# 2. Helper Functions
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
st.caption("Powered by FFmpeg, Groq Whisper v3, and Llama 3.3 70B")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Whisper Model", "Large v3")
col2.metric("Translation LLM", "Llama 3.3 70B")
col3.metric("Supported Formats", "MP4, MP3, WAV, MKV")
col4.metric("Output Files", ".SRT / .TXT")

st.markdown("---")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("📥 Input & Options")
    target_lang = st.selectbox(
        "Select Target Language for Subtitles",
        ["English", "Spanish", "French", "German", "Japanese", "Chinese", "Arabic", "Hindi", "Urdu"]
    )
    uploaded_file = st.file_uploader(
        "Upload Video or Audio File", 
        type=["mp4", "mp3", "wav", "mkv", "mov", "flac"]
    )
    process_btn = st.button("🚀 Process Media", type="primary", use_container_width=True)

with col_right:
    st.subheader("📝 Subtitle Studio Output")
    st.info("Uploaded content outputs and generated .srt timestamps will appear here once processed.")

# ----------------------------------------------------
# 4. Processing Execution (Direct & Unrestricted)
# ----------------------------------------------------
if process_btn:
    if not uploaded_file:
        st.error("Please upload a video or audio file first!")
    else:
        api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
        if not api_key:
            st.error("GROQ_API_KEY is missing from secrets.")
        else:
            client = Groq(api_key=api_key)
            status = st.empty()
            
            try:
                ext = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_input_path = tmp.name

                status.info("⏳ Step 1/3: Extracting audio via FFmpeg...")
                audio_path = extract_audio(tmp_input_path)

                status.info("⏳ Step 2/3: Transcribing audio with Groq Whisper v3...")
                with open(audio_path, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), f.read()),
                        model="whisper-large-v3",
                        response_format="verbose_json",
                    )

                status.info("⏳ Step 3/3: Formatting subtitles & translating via Llama 3.3...")
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

                if os.path.exists(tmp_input_path):
                    os.remove(tmp_input_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)

                status.empty()

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

# ----------------------------------------------------
# 5. Public FAQ Section
# ----------------------------------------------------
st.markdown("<br><hr><br>", unsafe_allow_html=True)
st.subheader("💡 Frequently Asked Questions & Features")

faq_col1, faq_col2 = st.columns(2)

with faq_col1:
    with st.expander("❓ How does the subtitle generation work?"):
        st.write("When you upload a video or audio file, FFmpeg extracts the audio track locally. The audio is sent to Groq's Whisper v3 engine for fast transcription, and translated using Llama 3.3.")

    with st.expander("❓ Which file formats are supported?"):
        st.write("We support `.mp4`, `.mp3`, `.wav`, `.mkv`, `.mov`, and `.flac` files up to Streamlit's standard upload limit.")

    with st.expander("❓ Do I need an account to generate subtitles?"):
        st.write("No account or login is required. You can upload media and download your `.srt` and `.txt` files instantly.")

with faq_col2:
    with st.expander("❓ Can I translate subtitles to other languages?"):
        st.write("Yes! You can choose from English, Spanish, French, German, Japanese, Chinese, Arabic, Hindi, and Urdu.")

    with st.expander("❓ What download formats are provided?"):
        st.write("You receive both standard `.srt` files and clean `.txt` full transcriptions.")

    with st.expander("❓ Are my uploaded files saved on the server?"):
        st.write("No. Files are deleted immediately after subtitle generation.")
