import streamlit as st
from groq import Groq
import os
import tempfile
import datetime
import subprocess

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & DARK THEME STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Subtitle Studio Pro | Free Automated Subtitles & Translations",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/subtitle-generator',
        'About': "# AI Subtitle Studio Pro\nGenerate, translate, and export `.srt` and `.txt` subtitles powered by Whisper v3 and Llama 3.3."
    }
)

# Custom High-Contrast Dark Styling
st.markdown("""
<style>
/* Main Canvas Dark Background */
.stApp {
    background-color: #0e1117 !important;
}

/* Bright Typography */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
    font-weight: 700 !important;
}

p, span, label, li {
    color: #e6edf3 !important;
}

/* Glassmorphic Container Cards */
div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
    background: #161b22 !important;
    border-radius: 12px !important;
    border: 1px solid #30363d !important;
    padding: 1.5rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
}

/* Primary Action Button */
.stButton > button {
    background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1rem !important;
    box-shadow: 0 2px 8px rgba(46, 160, 67, 0.4) !important;
    transition: all 0.2s ease-in-out !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(46, 160, 67, 0.6) !important;
}

/* Download Buttons */
div[data-testid="stDownloadButton"] > button {
    background: #21262d !important;
    color: #58a6ff !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

div[data-testid="stDownloadButton"] > button:hover {
    background: #30363d !important;
    border-color: #58a6ff !important;
}

/* Input Fields & Dropdowns */
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    background-color: #0d1117 !important;
    border-color: #30363d !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def format_timestamp(seconds: float) -> str:
    """Formats seconds into standard SRT timestamp format: HH:MM:SS,mmm"""
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def extract_audio(input_file_path: str) -> str:
    """Extracts and converts input MP4 video or audio files to an optimized MP3 audio track using FFmpeg."""
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_audio_path = temp_audio.name
    temp_audio.close()

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ar", "16000",
        "-ac", "1",
        "-q:a", "2",
        temp_audio_path
    ]
    
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        raise Exception(f"FFmpeg MP4-to-audio extraction failed: {process.stderr.decode('utf-8')}")
        
    return temp_audio_path

def translate_text(client: Groq, text: str, target_language: str) -> str:
    """Translates text to target language using Groq Llama 3.3 model."""
    if target_language.lower() == "english":
        return text

    prompt = f"Translate the following subtitle text to {target_language}. Maintain original tone and context. Output ONLY the translated text without extra explanation:\n\n{text}"
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()

# -----------------------------------------------------------------------------
# 3. HEADER & HERO SECTION
# -----------------------------------------------------------------------------
st.title("🎬 AI Subtitle Studio Pro")
st.markdown("#### *Generate, Translate, and Export Subtitles instantly powered by Whisper v3 and Llama 3.3*")
st.divider()

col_desc1, col_desc2 = st.columns(2)
with col_desc1:
    st.markdown("""
    ### ⚡ Key Features:
    * **MP4 to Audio Converter:** Automatic background extraction converting MP4 video tracks directly into optimized audio format using FFmpeg.
    * **High-Accuracy Speech-to-Text:** Ultra-fast speech recognition powered by Groq **Whisper v3**.
    * **Instant Multilingual Translation:** Powered by **Llama 3.3 (70B)** to translate subtitles seamlessly into your selected target language.
    """)

with col_desc2:
    st.markdown("""
    ### 💡 Quick FAQ:
    * **Is it free?** Yes, completely free powered by Groq AI hardware acceleration.
    * **What formats are supported?** High-speed processing for MP4, MP3, WAV, MKV, MOV, FLAC, and OGG formats.
    * **What can I export?** Downloadable `.srt` and `.txt` format outputs.
    """)

st.divider()

# -----------------------------------------------------------------------------
# 4. APP INTERFACE & LOGIC
# -----------------------------------------------------------------------------
col_input, col_output = st.columns([1, 1])

with col_input:
    st.subheader("📥 Media Upload & Options")
    
    target_lang = st.selectbox(
        "Select Target Subtitle Language",
        ["English", "Spanish", "French", "German", "Japanese", "Chinese", "Arabic", "Hindi", "Urdu"]
    )
    
    uploaded_file = st.file_uploader(
        "Upload Video or Audio File (MP4, MP3, WAV, MKV, etc.)", 
        type=["mp4", "mp3", "wav", "mkv", "mov", "flac", "ogg", "m4a"]
    )
    
    process_btn = st.button("🚀 Process & Generate Subtitles", type="primary", use_container_width=True)

with col_output:
    st.subheader("📝 Subtitle Studio Output")
    
    if not uploaded_file and not process_btn:
        st.info("Upload any media file on the left, select target language, and click Process.")

# Process Execution
if process_btn:
    if not uploaded_file:
        st.error("Please upload a media file first!")
    else:
        api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
        
        if not api_key:
            st.error("Groq API key missing. Please add `GROQ_API_KEY` to Streamlit secrets.")
        else:
            client = Groq(api_key=api_key)
            status_box = st.empty()
            
            try:
                file_ext = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_input_path = tmp_file.name

                # 1. Extract audio via FFmpeg
                status_box.info("⏳ 1/3 Running FFmpeg MP4 to Audio Converter...")
                audio_path = extract_audio(tmp_input_path)

                # 2. Transcribe via Groq Whisper API
                status_box.info("⏳ 2/3 Transcribing speech with Whisper v3...")
                with open(audio_path, "rb") as file_to_transcribe:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), file_to_transcribe.read()),
                        model="whisper-large-v3",
                        response_format="verbose_json",
                    )

                # 3. Format Subtitles / Translate via Llama 3.3
                status_box.info("⏳ 3/3 Formatting subtitles and translating via Llama 3.3...")
                srt_content = ""
                txt_content = ""

                segments = getattr(transcription, 'segments', [])
                
                if segments:
                    for idx, segment in enumerate(segments, start=1):
                        start = format_timestamp(segment['start'])
                        end = format_timestamp(segment['end'])
                        text = segment['text'].strip()

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

                status_box.empty()

                # Output
                with col_output:
                    st.success("✨ Subtitles generated successfully!")
                    
                    st.text_area("SRT Preview", srt_content, height=260)
                    
                    dl_col1, dl_col2 = st.columns(2)
                    with dl_col1:
                        st.download_button(
                            label="📥 Download .SRT",
                            data=srt_content,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}.srt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    with dl_col2:
                        st.download_button(
                            label="📥 Download .TXT",
                            data=txt_content,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

            except Exception as e:
                status_box.empty()
                st.error(f"An error occurred during processing: {str(e)}")
