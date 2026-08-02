import streamlit as st
from groq import Groq
import os
import tempfile
import datetime
import subprocess

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & GLASSMORPHISM UI STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Subtitle Studio Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background: #0E1117;
        color: #E0E6ED;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Glassmorphism Card Container */
    .css-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Sleek Typography */
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(90deg, #6366F1, #A855F7, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #9CA3AF;
        margin-bottom: 25px;
    }
    
    /* Metric Card Customization */
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700;
        color: #818CF8;
    }
    
    /* Styled Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        padding: 10px 24px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
    }
    
    /* Live Status Badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. AUDIO CONVERSION & PROCESSING ENGINE (FFmpeg)
# -----------------------------------------------------------------------------
def extract_and_convert_audio(input_file_path: str) -> str:
    """Uses FFmpeg to extract & convert any audio/video into lightweight 16kHz mono FLAC."""
    output_audio_path = os.path.splitext(input_file_path)[0] + "_processed.flac"
    cmd = [
        "ffmpeg", "-y", "-i", input_file_path,
        "-ar", "16000", "-ac", "1", "-map", "0:a",
        "-c:a", "flac", output_audio_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_audio_path

def format_timestamp(seconds: float) -> str:
    """Converts seconds into official SRT timestamp format 00:00:00,000"""
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millisecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def translate_text(groq_client, text: str, target_lang: str) -> str:
    """Translates subtitle segments into the target language using Llama-3.3-70b."""
    if target_lang == "Original Audio Language":
        return text
        
    prompt = (
        f"Translate the following subtitle text accurately to {target_lang}. "
        "Return ONLY the direct translation text without quotes or commentary:\n\n"
        f"{text}"
    )
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# -----------------------------------------------------------------------------
# 3. NATIVE PERSISTENT AUTHENTICATION GATE
# -----------------------------------------------------------------------------
if not st.user.is_logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="css-card" style="text-align: center;">
            <h1 class="main-title">🔒 AI Subtitle Studio</h1>
            <p class="sub-title">Automated multilingual subtitle generation powered by Groq & Whisper v3</p>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 20px 0;">
            <p style="color: #D1D5DB;">Sign in to access the studio dashboard. Your session will remain remembered automatically.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.button("🔑 Continue with Google", on_click=st.login, type="primary", use_container_width=True)
    
    st.stop()

# -----------------------------------------------------------------------------
# 4. MAIN DASHBOARD (USER IS LOGGED IN)
# -----------------------------------------------------------------------------
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# Sidebar Controls
with st.sidebar:
    st.markdown(f"### 👤 {st.user.name}")
    st.markdown(f"*{st.user.email}*")
    st.markdown('<span class="status-badge">● Google Session Active</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("⚙️ Output Settings")
    export_format = st.radio("Subtitle Format", ["SubRip (.srt)", "Plain Text (.txt)"])
    
    st.markdown("---")
    st.button("Log Out", on_click=st.logout, use_container_width=True, type="secondary")

# Page Header
st.markdown('<h1 class="main-title">🎬 AI Subtitle Studio Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Automated Media Converter, Whisper Transcription & Llama Multi-Language Translation</p>', unsafe_allow_html=True)

# App Metrics
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="Audio Converter", value="FFmpeg 16kHz", delta="Auto Mono")
with m2:
    st.metric(label="Speech-to-Text", value="Whisper v3", delta="Groq Accelerated")
with m3:
    st.metric(label="Translation Engine", value="Llama 3.3 70B", delta="Multilingual")

st.markdown("<br>", unsafe_allow_html=True)

# Dual Column App Workflow
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.markdown("### 📥 Media Upload & Options")
    
    target_languages = [
        "Original Audio Language", "English", "Urdu", "Spanish", 
        "French", "German", "Japanese", "Chinese", "Arabic", "Hindi"
    ]
    
    selected_target_lang = st.selectbox("Select Target Subtitle Language", target_languages)
    uploaded_file = st.file_uploader(
        "Upload Video or Audio File", 
        type=["mp4", "mp3", "wav", "m4a", "mov", "mkv", "flac", "ogg"]
    )
    
    if uploaded_file:
        st.success(f"File **{uploaded_file.name}** ready ({round(uploaded_file.size / (1024 * 1024), 2)} MB)")
        if uploaded_file.type.startswith("video"):
            st.video(uploaded_file)
        else:
            st.audio(uploaded_file)
            
        generate_btn = st.button("🚀 Process & Generate Subtitles", type="primary", use_container_width=True)

with right_col:
    st.markdown("### 📝 Subtitle Studio Output")
    
    if uploaded_file and 'generate_btn' in locals() and generate_btn:
        if not GROQ_API_KEY:
            st.error("Missing `GROQ_API_KEY` in Streamlit Secrets configuration!")
        else:
            groq_client = Groq(api_key=GROQ_API_KEY)
            tmp_path = None
            processed_audio_path = None
            
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name

                # 1. FFmpeg Conversion Pipeline
                with st.spinner("🎙️ Extracting & optimizing audio track with FFmpeg..."):
                    processed_audio_path = extract_and_convert_audio(tmp_path)

                # 2. Whisper v3 Transcription
                with st.spinner("⚡ Processing audio with Groq Whisper-large-v3..."):
                    with open(processed_audio_path, "rb") as audio_file:
                        transcript = groq_client.audio.transcriptions.create(
                            file=(os.path.basename(processed_audio_path), audio_file.read()),
                            model="whisper-large-v3",
                            response_format="verbose_json"
                        )
                    
                    segments = transcript.segments if hasattr(transcript, 'segments') else transcript.get('segments', [])
                    
                    srt_output = []
                    txt_output = []
                    
                    progress_bar = st.progress(0, text="Translating segments...")
                    total_segments = len(segments)
                    
                    # 3. Translation & Subtitle Formatting Loop
                    for idx, segment in enumerate(segments):
                        start_sec = segment.get('start', 0) if isinstance(segment, dict) else segment.start
                        end_sec = segment.get('end', 0) if isinstance(segment, dict) else segment.end
                        raw_text = (segment.get('text', '') if isinstance(segment, dict) else segment.text).strip()
                        
                        start_time = format_timestamp(start_sec)
                        end_time = format_timestamp(end_sec)
                        
                        final_text = translate_text(groq_client, raw_text, selected_target_lang)
                        
                        srt_entry = f"{idx + 1}\n{start_time} --> {end_time}\n{final_text}\n"
                        srt_output.append(srt_entry)
                        txt_output.append(final_text)
                        
                        if total_segments > 0:
                            progress_bar.progress((idx + 1) / total_segments, text=f"Processing line {idx+1}/{total_segments}...")
                    
                    progress_bar.empty()
                    final_subtitles = "\n".join(srt_output) if "SubRip" in export_format else "\n".join(txt_output)
                    
                    # Render Output
                    st.markdown(f"#### Generated Subtitles ({selected_target_lang}):")
                    st.text_area("Result Preview", final_subtitles, height=300)
                    
                    file_ext = ".srt" if "SubRip" in export_format else ".txt"
                    st.download_button(
                        label="📥 Download Subtitle File",
                        data=final_subtitles,
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{selected_target_lang}{file_ext}",
                        mime="text/plain",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"Error during audio processing: {str(e)}")
            finally:
                # Cleanup temp files
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
                if processed_audio_path and os.path.exists(processed_audio_path):
                    os.remove(processed_audio_path)
    else:
        st.info("Upload any media file on the left, select target language, and click **Process**.")
