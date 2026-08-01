import streamlit as st
from groq import Groq
import tempfile
import os

# Page Configuration
st.set_page_config(page_title="AI Subtitle Generator", page_icon="🎬", layout="centered")

st.title("🎬 Fast AI Subtitle Generator")
st.write("Generate `.srt` subtitles for your audio or video in seconds.")

# Sidebar for Groq API Key input
api_key = st.sidebar.text_input("Enter Groq API Key", type="password")

# File Upload Dropzone
uploaded_file = st.file_uploader("Upload Audio or Video File", type=["mp3", "wav", "mp4", "m4a"])

if uploaded_file is not None:
    st.success(f"File attached: {uploaded_file.name}")
    
    if st.button("🚀 Generate Subtitles", type="primary"):
        if not api_key:
            st.error("Please enter your Groq API Key in the left sidebar first!")
        else:
            with st.spinner("Processing audio with Groq AI..."):
                try:
                    # Save temporary file to process
                    suffix = os.path.splitext(uploaded_file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = tmp_file.name

                    # Connect to Groq AI engine
                    client = Groq(api_key=api_key)
                    with open(tmp_path, "rb") as file:
                        transcription = client.audio.transcriptions.create(
                            file=(uploaded_file.name, file.read()),
                            model="whisper-large-v3-turbo",
                            response_format="verbose_json"
                        )

                    # Timestamp formatter to convert seconds into standard SRT format
                    def format_timestamp(seconds: float) -> str:
                        hours = int(seconds // 3600)
                        minutes = int((seconds % 3600) // 60)
                        secs = int(seconds % 60)
                        millis = int((seconds - int(seconds)) * 1000)
                        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

                    srt_content = ""
                    for i, segment in enumerate(transcription.segments, start=1):
                        start_time = format_timestamp(segment['start'])
                        end_time = format_timestamp(segment['end'])
                        text = segment['text'].strip()
                        srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"

                    # Delete temp file
                    os.remove(tmp_path)

                    # Display results & download button
                    st.subheader("Subtitles Ready!")
                    st.text_area("Preview Subtitles", srt_content, height=200)

                    st.download_button(
                        label="📥 Download .SRT File",
                        data=srt_content,
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}.srt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"Error encountered: {e}")
