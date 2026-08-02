import streamlit as st
from groq import Groq
import tempfile
import subprocess
import os

# Function to convert Groq's verbose_json segments to SRT format
def convert_to_srt(segments):
    srt_output = ""
    for idx, segment in enumerate(segments, start=1):
        start = segment['start']
        end = segment['end']
        text = segment['text'].strip()

        # Format timestamps into HH:MM:SS,mmm
        def format_time(seconds):
            hrs = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            msecs = int((seconds % 1) * 1000)
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"

        start_str = format_time(start)
        end_str = format_time(end)

        srt_output += f"{idx}\n{start_str} --> {end_str}\n{text}\n\n"
    
    return srt_output

# 1. Page Config
st.set_page_config(
    page_title="AI Subtitle Studio Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Rich & Modern Custom CSS
st.markdown("""
    <style>
    /* Dark Theme Background */
    .stApp {
        background: linear-gradient(135deg, #0B0E14 0%, #161B22 100%);
        color: #E6EDF3;
    }
    
    /* Hero Header Banner */
    .hero-container {
        background: linear-gradient(90deg, #1F2937 0%, #111827 100%);
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid rgba(0, 242, 254, 0.2);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(45deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        color: #9CA3AF;
        font-size: 1.1rem;
    }

    /* Cards & Containers */
    .custom-card {
        background: rgba(22, 27, 34, 0.75);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    /* File Uploader styling */
    [data-testid="stFileUploader"] {
        border: 2px dashed #00F2FE !important;
        border-radius: 12px !important;
        background-color: #0D1117 !important;
        padding: 15px !important;
    }

    /* Action Button styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(45deg, #00F2FE 0%, #4FACFE 100%);
        color: #000000;
        border: none;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: 700;
        padding: 0.8rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 242, 254, 0.5);
        color: #000000;
    }

    /* Textarea SRT styling */
    textarea {
        background-color: #0D1117 !important;
        color: #00FF87 !important;
        border: 1px solid #30363D !important;
        border-radius: 10px !important;
        font-family: 'Fira Code', 'Courier New', monospace !important;
        font-size: 0.95rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Hero Header
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">⚡ Fast AI Subtitle Studio</div>
        <div class="hero-subtitle">High-speed video subtitle generation & translation powered by Groq Whisper</div>
    </div>
""", unsafe_allow_html=True)

# 4. Initialize Groq Client
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("⚠️ API Key missing from `st.secrets`! Add `GROQ_API_KEY` to your Streamlit secrets.")
    st.stop()

# 5. UI Layout in 2 Columns
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### 📥 1. Upload & Settings")
    
    uploaded_file = st.file_uploader(
        "Drop your audio or video file here (up to 200MB)",
        type=["mp4", "mp3", "wav", "m4a", "mkv", "webm", "flv"]
    )
    
    language_options = {
        "English (Translate Foreign Audio)": "en_translate",
        "Original Audio Language (Auto-Detect)": "auto",
        "Japanese (日本語)": "ja",
        "Spanish (Español)": "es",
        "French (Français)": "fr",
        "German (Deutsch)": "de",
        "Urdu (اردو)": "ur",
        "Hindi (हिंदी)": "hi",
        "Chinese (中文)": "zh",
        "Arabic (العربية)": "ar"
    }

    target_lang_label = st.selectbox(
        "🌐 Target Subtitle Language:",
        options=list(language_options.keys())
    )
    selected_lang_code = language_options[target_lang_label]

    # Quick Info Box
    with st.expander("ℹ️ Supported Formats & Performance Info"):
        st.markdown("""
        * **Accepted Inputs:** MP4, MP3, WAV, M4A, MKV, WEBM.
        * **Engine:** Server-side `ffmpeg` conversion to 16kHz mono audio.
        * **Speed:** ~5-10 seconds processing for full episode files!
        """)

with col_right:
    st.markdown("### 📊 2. Media File Stats")
    
    if uploaded_file is not None:
        file_size_mb = round(uploaded_file.size / (1024 * 1024), 2)
        
        # Display Specs Grid
        m1, m2, m3 = st.columns(3)
        m1.metric("File Size", f"{file_size_mb} MB")
        m2.metric("Format", uploaded_file.name.split('.')[-1].upper())
        m3.metric("Target", selected_lang_code.split('_')[0].upper())
        
        st.info(f"📁 Ready to process: `{uploaded_file.name}`")
    else:
        st.markdown("""
            <div style="text-align: center; padding: 40px; border: 1px dashed #30363D; border-radius: 12px; color: #6E7681;">
                👈 Upload a file on the left to view file metadata and start subtitle extraction.
            </div>
        """, unsafe_allow_html=True)

# 6. Process Button & Execution
st.markdown("---")

if uploaded_file is not None:
    if st.button("🚀 Generate Subtitles Now"):
        with st.spinner("Processing file... Converting audio & running Whisper model..."):
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                temp_file.write(uploaded_file.read())
                input_path = temp_file.name

            mp3_path = input_path + "_converted.mp3"

            try:
                # Convert video/audio to compressed MP3
                cmd = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-vn", "-ar", "16000", "-ac", "1", "-b:a", "128k",
                    mp3_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Route API call based on language selection
                with open(mp3_path, "rb") as audio_file:
                    if selected_lang_code == "en_translate":
                        response = client.audio.translations.create(
                            file=audio_file,
                            model="whisper-large-v3",
                            response_format="verbose_json"
                        )
                    elif selected_lang_code == "auto":
                        response = client.audio.transcriptions.create(
                            file=audio_file,
                            model="whisper-large-v3-turbo",
                            response_format="verbose_json"
                        )
                    else:
                        response = client.audio.transcriptions.create(
                            file=audio_file,
                            model="whisper-large-v3-turbo",
                            language=selected_lang_code,
                            response_format="verbose_json"
                        )

                # Format to SRT
                srt_output = convert_to_srt(response.segments)

                st.success("🎉 Subtitles successfully generated!")

                # Results Layout (2 Columns: Download + Preview)
                res_col1, res_col2 = st.columns([1, 2])
                
                with res_col1:
                    st.markdown("### 📥 Export File")
                    st.download_button(
                        label="💾 Download `.srt` Subtitles",
                        data=srt_output,
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}_subtitles.srt",
                        mime="text/plain",
                    )
                
                with res_col2:
                    st.markdown("### 📝 SRT Preview")
                    st.text_area("Generated Output", srt_output, height=300)

            except subprocess.CalledProcessError:
                st.error("Error running ffmpeg conversion. Check `packages.txt` deployment.")
            except Exception as e:
                st.error(f"Error generating subtitles: {str(e)}")
            
            finally:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
