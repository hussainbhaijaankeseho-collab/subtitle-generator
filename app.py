import os
import subprocess
import tempfile
import streamlit as st
from groq import Groq

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Subtitle Studio Pro | Free Translation & Generation",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- High-Contrast Dark Theme Styling & SEO Enhancements ---
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0d1117;
            color: #f0f6fc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }
        .glass-card {
            background: rgba(22, 27, 34, 0.7);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        h1, h2, h3 {
            color: #58a6ff !important;
            font-weight: 700;
        }
        p, label, span, .stMarkdown {
            color: #c9d1d9 !important;
        }
        .stButton>button {
            background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
            box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
        }
        .streamlit-expanderHeader {
            background-color: #161b22 !important;
            border: 1px solid #30363d;
            border-radius: 8px;
            color: #58a6ff !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <head>
        <meta name="description" content="AI Subtitle Studio Pro - Free online automatic subtitle generator, video transcription using Groq Whisper v3, and multi-language translation powered by Llama 3.">
        <meta name="keywords" content="subtitle generator, AI subtitle creator, video to text, speech to text, translation, Groq Whisper, Llama 3, Streamlit app">
        <meta name="author" content="AI Subtitle Studio Pro">
    </head>
    """,
    unsafe_allow_html=True,
)

# --- Helper Functions ---
def get_media_metadata(input_file_path):
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", input_file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        
        duration = float(data.get("format", {}).get("duration", 0))
        audio_languages = [
            f"{s.get('codec_name', 'unknown')} (Lang: {s.get('tags', {}).get('language', 'unknown').lower()})"
            for s in data.get("streams", []) if s.get("codec_type") == "audio"
        ]
        return {"duration": duration, "audio_streams": audio_languages if audio_languages else ["Default Audio Track"]}
    except Exception:
        return {"duration": 0, "audio_streams": ["Standard Audio Track"]}

def extract_audio(input_file_path, output_audio_path):
    cmd = [
        "ffmpeg", "-y", "-i", input_file_path,
        "-vn", "-acodec", "libmp3lame", "-ar", "16000", "-ac", "1", output_audio_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

def chunk_text_by_lines(text, max_lines=60):
    lines = text.split("\n")
    chunks, current_chunk = [], []
    for line in lines:
        current_chunk.append(line)
        if len(current_chunk) >= max_lines:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    return chunks

# --- Main Sidebar UI ---
with st.sidebar:
    st.markdown("## ⚙️ Studio Controls")
    api_key_input = st.text_input("Enter Groq API Key", type="password")
    
    st.markdown("---")
    st.markdown("### 🤖 Model Configurations")
    selected_model = st.selectbox("Select Translation Model", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"], index=0)
    target_language = st.selectbox("Target Translation Language", ["English", "Urdu", "Spanish", "French", "German", "Arabic", "Hindi", "Chinese", "Japanese"], index=0)
    export_format = st.selectbox("Subtitle Export Format", [".srt", ".vtt", ".txt"], index=0)

    st.markdown("---")
    st.markdown("### 📊 Web App Info")
    st.info("**Status:** Online & Public\n\n**Engine:** Groq Whisper v3 + Llama 3")

# --- Main Application Layout ---
st.markdown(
    """
    <div class="glass-card">
        <h1>🎬 AI Subtitle Studio Pro</h1>
        <p>Transform your video and audio files into precise transcripts, run smart FFmpeg track analysis, and translate subtitles instantly using cutting-edge open-source AI models entirely for free.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("Upload Video or Audio File", type=["mp4", "mkv", "mov", "mp3", "wav", "m4a"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
    tfile.write(uploaded_file.read())
    tfile.close()

    with st.spinner("Analyzing media streams and metadata via FFmpeg..."):
        metadata = get_media_metadata(tfile.name)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="glass-card"><h3>📁 File Overview</h3><p><b>Filename:</b> {uploaded_file.name}</p><p><b>Duration:</b> {round(metadata["duration"], 2)} seconds</p></div>', unsafe_allow_html=True)
    with col2:
        tracks = "".join([f"<li>{stream}</li>" for stream in metadata['audio_streams']])
        st.markdown(f'<div class="glass-card"><h3>🔍 Track Language Analysis</h3><ul>{tracks}</ul></div>', unsafe_allow_html=True)

    if st.button("🚀 Generate & Translate Subtitles"):
        if not api_key_input:
            st.error("Please provide a valid Groq API Key in the sidebar.")
        else:
            try:
                client = Groq(api_key=api_key_input)
                audio_path = tfile.name + ".mp3"

                # Step 1: Audio Extraction
                progress_bar = st.progress(0)
                st.info("Step 1/3: Extracting clean audio track via FFmpeg...")
                extract_audio(tfile.name, audio_path)
                progress_bar.progress(33)

                # Step 2: Transcription
                st.info("Step 2/3: Transcribing audio utilizing Groq Whisper v3...")
                with open(audio_path, "rb") as file_to_transcribe:
                    raw_subtitles = client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), file_to_transcribe.read()),
                        model="whisper-large-v3",
                        response_format="srt",
                    )
                progress_bar.progress(66)

                # Step 3: Translation
                translated_output = raw_subtitles
                if target_language != "English":
                    st.info(f"Step 3/3: Translating subtitles into {target_language} using {selected_model} (Smart Chunking active)...")
                    chunks = chunk_text_by_lines(raw_subtitles, max_lines=50)
                    translated_chunks = []
                    for chunk in chunks:
                        prompt = f"Translate the following subtitle blocks into {target_language}. Maintain the precise SRT timestamps, sequence numbers, and formatting layout. Do not add introductory text:\n\n{chunk}"
                        response = client.chat.completions.create(
                            model=selected_model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2,
                        )
                        translated_chunks.append(response.choices[0].message.content)
                    translated_output = "\n\n".join(translated_chunks)

                progress_bar.progress(100)
                st.success("Subtitle processing and translation completed successfully!")

                # Formatting
                final_content = translated_output
                mime_type = "text/plain"
                if export_format == ".vtt":
                    final_content = "WEBVTT\n\n" + final_content.replace(",", ".")
                    mime_type = "text/vtt"

                st.markdown('<div class="glass-card"><h3>📝 Result Preview</h3></div>', unsafe_allow_html=True)
                st.text_area("Subtitle Data Viewer", final_content, height=300)

                output_filename = os.path.splitext(uploaded_file.name)[0] + f"_{target_language.lower()}{export_format}"
                st.download_button(label=f"📥 Download Subtitles ({export_format})", data=final_content, file_name=output_filename, mime=mime_type)

                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if os.path.exists(tfile.name):
        os.remove(tfile.name)

st.markdown("---")
with st.expander("❓ Frequently Asked Questions & Platform Guide"):
    st.markdown("""
    * **How does AI Subtitle Studio Pro process media?** The app uses local FFmpeg binaries to extract audio, Groq's Whisper v3 for transcription, and Llama 3 for translation.
    * **What is Smart Chunking?** Smart chunking breaks large files into smaller segments before translation to protect against free-tier Token-Per-Minute errors.
    """)
