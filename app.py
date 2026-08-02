import streamlit as st
from groq import Groq
import os
import tempfile
import datetime
import subprocess

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CLEAN UI STYLING
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

# High-contrast, crystal clear UI styling
st.markdown("""
<style>
/* Main Background */
.stApp {
    background-color: #0d1117;
}

/* Headings and Text Color Fixes */
h1, h2, h3, h4, h5, h6 {
    color: #f0f6fc !important;
    font-weight: 700 !important;
}

p, span, label, li {
    color: #c9d1d9 !important;
}

/* Accent Header Styling */
.title-accent {
    color: #58a6ff !important;
}

/* Card Boxes */
div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
    background: #161b22;
    border-radius: 10px;
    border: 1px solid #30363d;
    padding: 1.5rem;
}

/* Buttons Styling */
.stButton > button {
    background-color: #238636 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1rem !important;
    transition: background-color 0.2s ease-in-out !important;
}

.stButton > button:hover {
    background-color: #2ea043 !important;
}

/* Download Buttons Accent */
div[data-testid="stDownloadButton"] > button {
    background-color: #21262d !important;
    color: #58a6ff !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
}

div[data-testid="stDownloadButton"] > button:hover {
    background-color: #30363d !important;
    border-color: #8b949e !important;
}

/* Input & Select Box styling */
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    background-color: #0d1117 !important;
    border-color: #30363d !important;
    color: #f0f6fc !important;
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
    """Extracts/converts input video or audio to an optimized MP3 audio format using FFmpeg."""
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
        raise Exception(f"FFmpeg audio extraction failed: {process.stderr.decode('utf-8')}")
        
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
st.markdown("#### *Generate, Translate, and Export Subtitles instantly powered by Groq AI*")
st.divider()

col_desc1, col_desc2 = st.columns(2)
with col_desc1:
    st.markdown("""
    ### ⚡ Key Features
    * **High-Accuracy Speech-to-Text:** Extract audio directly from MP4, MP3, WAV, MKV, and FLAC files.
    * **Automated Audio Pre-Processing:** Integrated FFmpeg audio extraction & optimization.
    * **Instant Multilingual Translation:** Automatically translate speech to target languages via Llama 3.3.
    """)

with col_desc2:
    st.markdown("""
    ### 💡 Quick FAQ
    * **Is it free?** Yes, powered by Groq's high-speed AI inference.
    * **What formats are supported?** MP4, MP3, WAV, MKV, MOV, FLAC, and OGG formats.
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
        "Upload Video or Audio File", 
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
        # Check API key from secret or environment
        api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
        
        if not api_key:
            st.error("Groq API key missing. Please add `GROQ_API_KEY` to Streamlit secrets.")
        else:
            client = Groq(api_key=api_key)
            status_box = st.empty()
            
            try:
                # Save uploaded file temporarily
                file_ext = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_input_path = tmp_file.name

                # 1. Extract audio via FFmpeg
                status_box.info("⏳ 1/3 Extracting and optimizing audio track...")
                audio_path = extract_audio(tmp_input_path)

                # 2. Transcribe via Groq Whisper API
                status_box.info("⏳ 2/3 Transcribing audio with Whisper...")
                with open(audio_path, "rb") as file_to_transcribe:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), file_to_transcribe.read()),
                        model="whisper-large-v3",
                        response_format="verbose_json",
                    )

                # 3. Format Subtitles / Translate
                status_box.info("⏳ 3/3 Formatting subtitles and applying translation...")
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

                # Clean up temp files
                if os.path.exists(tmp_input_path):
                    os.remove(tmp_input_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)

                status_box.empty()

                # Display outputs on right column
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
