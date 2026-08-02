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

# 1. Custom Styling (Modern Dark Mode UI)
st.set_page_config(
    page_title="AI Subtitle Generator",
    page_icon="🎬",
    layout="centered"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    h1 {
        color: #00F2FE;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
    }
    
    [data-testid="stFileUploader"] {
        border: 2px dashed #00F2FE;
        border-radius: 12px;
        padding: 20px;
        background-color: #161B22;
    }

    .stButton > button {
        background: linear-gradient(45deg, #4FACFE 0%, #00F2FE 100%);
        color: #000000;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.6rem 2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.4);
        color: #000000;
    }

    textarea {
        background-color: #161B22 !important;
        color: #00FF87 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        font-family: 'Courier New', monospace !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Header Section
st.title("🎬 Fast AI Subtitle Generator")
st.write("Generate `.srt` subtitles from your video or audio files using Groq Whisper.")

# 3. Client Initialization
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("API Key not found in secrets! Please check your Streamlit app configuration.")
    st.stop()

# 4. File Upload
uploaded_file = st.file_uploader(
    "Upload Video or Audio (MP4, MP3, WAV, etc. up to 200MB)",
    type=["mp4", "mp3", "wav", "m4a", "mkv"]
)

if uploaded_file is not None:
    if st.button("🚀 Generate Subtitles"):
        with st.spinner("Processing file... Extracting audio & generating subtitles..."):
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                temp_file.write(uploaded_file.read())
                input_path = temp_file.name

            mp3_path = input_path + "_converted.mp3"

            try:
                # Convert to lightweight MP3 using ffmpeg
                cmd = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-vn", "-ar", "16000", "-ac", "1", "-b:a", "128k",
                    mp3_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Send to Groq Whisper API with response_format="verbose_json"
                with open(mp3_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3-turbo",
                        response_format="verbose_json"
                    )

                # Convert JSON segments to SRT
                srt_output = convert_to_srt(response.segments)

                st.success("✨ Subtitles successfully generated!")
                
                # Download Button
                st.download_button(
                    label="📥 Download Subtitles (.srt)",
                    data=srt_output,
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}.srt",
                    mime="text/plain"
                )

                # SRT Output Preview
                st.subheader("Subtitle Preview")
                st.text_area("Generated SRT Output", srt_output, height=250)

            except subprocess.CalledProcessError as e:
                st.error("Error converting media with ffmpeg. Check packages.txt deployment.")
            except Exception as e:
                st.error(f"Error generating subtitles: {str(e)}")
            
            finally:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
