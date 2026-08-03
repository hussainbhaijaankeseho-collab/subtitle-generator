import json
import os
import subprocess
import tempfile
import streamlit as st
from groq import Groq

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Subtitle Studio Pro | Multi-Language Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- High-Contrast Dark Theme CSS ---
st.markdown(
    """
    <style>
        .stApp {
            background-color: #080b11;
            color: #e6edf3;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        [data-testid="stSidebar"] {
            background-color: #0d1117;
            border-right: 1px solid #21262d;
        }
        
        /* Modern Glass Card */
        .glass-card {
            background: rgba(13, 17, 23, 0.85);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }
        
        .badge {
            background-color: #1f6feb22;
            color: #58a6ff;
            border: 1px solid #1f6feb;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 10px;
        }
        
        /* Typography */
        h1, h2, h3 {
            color: #58a6ff !important;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        p, label, span, .stMarkdown {
            color: #c9d1d9 !important;
        }
        
        /* Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
            color: #ffffff;
            font-weight: 700;
            border: 1px solid #3fb950;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 1rem;
            width: 100%;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 4px 12px rgba(46, 160, 67, 0.2);
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
            box-shadow: 0 6px 16px rgba(46, 160, 67, 0.4);
            transform: translateY(-1px);
        }
        
        .streamlit-expanderHeader {
            background-color: #0d1117 !important;
            border: 1px solid #30363d;
            border-radius: 8px;
            color: #58a6ff !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Metadata Injection ---
st.markdown(
    """
    <head>
        <meta name="description" content="AI Subtitle Studio Pro - Automatic subtitle generator, FFmpeg media analysis, Groq Whisper v3 transcription, and Llama 3 translation.">
        <meta name="keywords" content="subtitle studio, video to srt, whisper v3, llama 3 subtitle translator, ffmpeg media transcoder">
    </head>
    """,
    unsafe_allow_html=True,
)

# --- Language Mappings ---
SOURCE_LANGUAGES = {
    "🌐 Auto-Detect Language": None,
    "English": "en",
    "Urdu": "ur",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Arabic": "ar",
    "Hindi": "hi",
    "Japanese": "ja",
    "Chinese": "zh",
    "Russian": "ru",
    "Turkish": "tr",
    "Italian": "it",
    "Korean": "ko",
    "Portuguese": "pt",
}

TARGET_LANGUAGES = [
    "Original (No Translation)",
    "Urdu",
    "English",
    "Spanish",
    "French",
    "German",
    "Arabic",
    "Hindi",
    "Japanese",
    "Chinese",
    "Russian",
    "Turkish",
    "Italian",
    "Korean",
    "Portuguese",
    "Dutch",
    "Persian",
]


# --- Helper Functions ---
def get_media_metadata(input_file_path):
  """Analyzes media details, codecs, and durations using FFprobe."""
  try:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        input_file_path,
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)

    duration = float(data.get("format", {}).get("duration", 0))
    streams = []
    for s in data.get("streams", []):
      if s.get("codec_type") == "audio":
        codec = s.get("codec_name", "unknown")
        lang = s.get("tags", {}).get("language", "auto").lower()
        streams.append(f"Audio Track #{s.get('index')}: {codec} (lang: {lang})")

    return {
        "duration": duration,
        "audio_streams": streams if streams else ["Default Audio Track"],
    }
  except Exception:
    return {"duration": 0, "audio_streams": ["Standard Audio Track"]}


def extract_audio(input_file_path, output_audio_path):
  """Extracts 16kHz mono audio via FFmpeg."""
  cmd = [
      "ffmpeg",
      "-y",
      "-i",
      input_file_path,
      "-vn",
      "-acodec",
      "libmp3lame",
      "-ar",
      "16000",
      "-ac",
      "1",
      output_audio_path,
  ]
  subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def chunk_text_by_lines(text, max_lines=50):
  """Splits transcription into line chunks to prevent Groq rate limits."""
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


def srt_to_txt(srt_content):
  """Strips SRT sequence numbers and timestamps to output clean text."""
  lines = srt_content.split("\n")
  clean_lines = []
  for line in lines:
    line_str = line.strip()
    if line_str.isdigit() or "-->" in line_str:
      continue
    if line_str:
      clean_lines.append(line_str)
  return "\n".join(clean_lines)


# --- Sidebar UI ---
with st.sidebar:
  st.markdown("## ⚙️ Engine Controls")
  api_key_input = st.text_input(
      "Groq API Key", type="password", help="Enter key from console.groq.com"
  )

  st.markdown("---")
  st.markdown("### 🗣️ Language Options")

  # Source Language Selector for Whisper
  selected_source_lang_label = st.selectbox(
      "Source Audio Language",
      list(SOURCE_LANGUAGES.keys()),
      index=0,
      help="Specify spoken audio language to boost transcription precision.",
  )
  source_lang_code = SOURCE_LANGUAGES[selected_source_lang_label]

  # Target Language Selector for Translation
  target_language = st.selectbox(
      "Target Translation Language",
      TARGET_LANGUAGES,
      index=0,
      help="Select language to translate subtitles into using Llama 3.",
  )

  st.markdown("---")
  st.markdown("### 🤖 Model Settings")
  whisper_model = st.selectbox(
      "Whisper Transcription Model",
      ["whisper-large-v3", "whisper-large-v3-turbo"],
      index=0,
  )
  translation_model = st.selectbox(
      "Llama Translation Model",
      ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"],
      index=0,
      help=(
          "8b-instant is recommended for fast execution and high rate-limit"
          " thresholds."
      ),
  )

  export_format = st.selectbox(
      "Subtitle Export Format", [".srt", ".vtt", ".txt"], index=0
  )

  st.markdown("---")
  st.markdown(
      "**Platform Version:** 3.0 Pro\n\n**Infrastructure:** Streamlit + Groq"
      " Cloud"
  )


# --- Main Dashboard ---
st.markdown(
    """
    <div class="glass-card">
        <span class="badge">PRO EDITION</span>
        <h1>🎬 AI Subtitle Studio Pro</h1>
        <p>Generate, edit, and translate video and audio subtitles in multi-languages using FFmpeg, Groq Whisper v3, and Llama 3 models.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Upload File Card
uploaded_file = st.file_uploader(
    "Select Audio or Video File",
    type=["mp4", "mkv", "mov", "avi", "mp3", "wav", "m4a"],
    help="Supports popular video and audio files.",
)

if uploaded_file is not None:
  tfile = tempfile.NamedTemporaryFile(
      delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
  )
  tfile.write(uploaded_file.read())
  tfile.close()

  # FFprobe Metadata Summary Cards
  with st.spinner("Analyzing media track specs via FFmpeg..."):
    metadata = get_media_metadata(tfile.name)

  col1, col2 = st.columns(2)
  with col1:
    st.markdown(
        f"""
            <div class="glass-card">
                <h3>📁 File Details</h3>
                <p><b>Name:</b> {uploaded_file.name}</p>
                <p><b>Duration:</b> {round(metadata['duration'], 2)} seconds</p>
                <p><b>Size:</b> {round(uploaded_file.size / (1024*1024), 2)} MB</p>
            </div>
            """,
        unsafe_allow_html=True,
    )
  with col2:
    tracks_html = "".join(
        [f"<li>{stream}</li>" for stream in metadata["audio_streams"]]
    )
    st.markdown(
        f"""
            <div class="glass-card">
                <h3>🎙️ Detected Audio Streams</h3>
                <ul>{tracks_html}</ul>
            </div>
            """,
        unsafe_allow_html=True,
    )

  # Run Action Button
  if st.button("🚀 Process Subtitles"):
    if not api_key_input:
      st.error("Please enter a valid Groq API Key in the left sidebar.")
    else:
      try:
        client = Groq(api_key=api_key_input)
        audio_path = tfile.name + ".mp3"

        # Progress tracking setup
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Step 1: Extract Audio
        status_text.info(
            "Step 1/3: Extracting clean 16kHz audio track via FFmpeg..."
        )
        extract_audio(tfile.name, audio_path)
        progress_bar.progress(33)

        # Step 2: Transcribe via Whisper
        status_text.info(
            f"Step 2/3: Transcribing audio with Groq {whisper_model}..."
        )
        with open(audio_path, "rb") as file_to_transcribe:
          transcribe_args = {
              "file": (os.path.basename(audio_path), file_to_transcribe.read()),
              "model": whisper_model,
              "response_format": "srt",
          }
          if source_lang_code:
            transcribe_args["language"] = source_lang_code

          raw_subtitles = client.audio.transcriptions.create(**transcribe_args)
        progress_bar.progress(66)

        # Step 3: Translate via Llama
        translated_output = raw_subtitles
        if target_language != "Original (No Translation)":
          status_text.info(
              f"Step 3/3: Translating subtitles into {target_language} using"
              f" {translation_model} (Smart Chunking)..."
          )
          chunks = chunk_text_by_lines(raw_subtitles, max_lines=50)
          translated_chunks = []

          for chunk in chunks:
            prompt = (
                f"Translate the following subtitle blocks into {target_language}."
                " Maintain exact SRT line numbers, timestamps, and formatting"
                f" structure. Output only SRT formatted text:\n\n{chunk}"
            )
            response = client.chat.completions.create(
                model=translation_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            translated_chunks.append(response.choices[0].message.content)

          translated_output = "\n\n".join(translated_chunks)

        progress_bar.progress(100)
        status_text.success("Processing completed successfully!")

        # Format Processing
        final_content = translated_output
        mime_type = "text/plain"

        if export_format == ".vtt":
          final_content = "WEBVTT\n\n" + final_content.replace(",", ".")
          mime_type = "text/vtt"
        elif export_format == ".txt":
          final_content = srt_to_txt(translated_output)
          mime_type = "text/plain"

        # Results Display & Download
        st.markdown(
            """
                <div class="glass-card">
                    <h3>📝 Subtitle Output</h3>
                </div>
                """,
            unsafe_allow_html=True,
        )
        st.text_area("Subtitle Contents", final_content, height=350)

        output_filename = (
            os.path.splitext(uploaded_file.name)[0]
            + f"_{target_language.lower().replace(' ', '_')}{export_format}"
        )

        st.download_button(
            label=f"📥 Download ({export_format.upper()})",
            data=final_content,
            file_name=output_filename,
            mime=mime_type,
        )

        # Clean audio temp file
        if os.path.exists(audio_path):
          os.remove(audio_path)

      except Exception as e:
        st.error(f"Processing Error: {e}")

  # Clean main temp file
  if os.path.exists(tfile.name):
    os.remove(tfile.name)

# Documentation Expander
st.markdown("---")
with st.expander("❓ Documentation & Optimization Notes"):
  st.markdown("""
    * **Source Audio Language:** Explicitly setting the spoken audio language improves Whisper's transcription accuracy and processing speed.
    * **Target Translation Language:** Selected target language is processed through Llama 3 models while retaining exact timecodes.
    * **Smart Chunking:** Segments long files into sub-50-line blocks to avoid Groq rate limits.
    """)
