import streamlit as st
import subprocess
import os
import tempfile
from groq import Groq

# 1. Fetch API key automatically from Streamlit Secrets or manual input
api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("Enter Groq API Key", type="password")

if not api_key:
    st.warning("Please provide a Groq API Key in Secrets or the sidebar to proceed.")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# 2. Fast MP4 to MP3 extraction function
def convert_mp4_to_mp3(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_mp4:
        tmp_mp4.write(video_file.getvalue())
        tmp_mp4_path = tmp_mp4.name

    tmp_mp3_path = tmp_mp4_path.replace(".mp4", ".mp3")

    # Extract audio fast at 128kbps (bypasses 25MB limit)
    command = [
        "ffmpeg", "-y",
        "-i", tmp_mp4_path,
        "-vn",
        "-b:a", "128k",
        "-ar", "44100",
        tmp_mp3_path
    ]
    
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Clean up input video immediately
    os.remove(tmp_mp4_path)

    return tmp_mp3_path


# 3. Streamlit Interface
st.title("⚡ Video Subtitle Generator")

uploaded_video = st.file_uploader("Upload MP4 Video (up to 200MB)", type=["mp4"])

if uploaded_video is not None:
    if st.button("Generate Subtitles"):
        
        # Step A: Convert to lightweight MP3
        with st.spinner("Extracting audio from video (2–5 secs)..."):
            mp3_path = convert_mp4_to_mp3(uploaded_video)

        # Step B: Pass directly to Groq Whisper
        with st.spinner("Transcribing with Whisper..."):
            with open(mp3_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=(os.path.basename(mp3_path), audio_file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="srt"  # Change to "verbose_json" or "text" if needed
                )

        # Clean up temporary MP3 file
        if os.path.exists(mp3_path):
            os.remove(mp3_path)

        st.success("Subtitles ready!")
        
        # Display subtitles
        st.subheader("Generated Subtitles")
        st.code(transcription, language="srt")

        # Provide subtitle download option
        st.download_button(
            label="Download .SRT Subtitle File",
            data=transcription,
            file_name="subtitles.srt",
            mime="text/plain"
        )
