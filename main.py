import streamlit as st
from google import genai
import time
import os
import shutil
import subprocess
import tempfile
import yt_dlp

# --- 1. App Config ---
st.set_page_config(page_title="BJJ Expert AI v2", layout="wide", page_icon="🥋")

if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'temp_files' not in st.session_state:
    st.session_state.temp_files = []

st.title("🥋 BJJ Advanced Technical Analysis (Gemini 2.5 Pro)")

# --- 2. Sidebar (Personalization) ---
with st.sidebar:
    st.header("⚙️ Settings & Profile")
    api_key = st.text_input("Gemini API Key", type="password")

    st.divider()
    st.subheader("👤 Your Style")
    belt_level = st.selectbox("Current Belt Level", ["White", "Blue", "Purple", "Brown", "Black"])
    favorite_moves = st.text_input("Favorite Guards/Moves (optional)", placeholder="e.g. De La Riva, Spider Guard, Triangle Choke")
    specific_concern = st.text_area("Specific Concerns / Focus Area (optional)", placeholder="e.g. framing against pass guard, timing for shrimp")

    st.divider()
    if st.button("Remove Loaded Video"):
        for f in st.session_state.temp_files:
            if os.path.exists(f):
                os.remove(f)
        st.session_state.temp_files = []
        st.session_state.video_path = None
        st.rerun()


# --- 3. Utility Functions ---
def find_ffmpeg():
    """Find ffmpeg using shutil.which (system PATH)."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    return "ffmpeg"


def compress_video(input_path, output_path):
    """Compress video to 480p for faster upload to Gemini."""
    ffmpeg_path = find_ffmpeg()
    try:
        cmd = [
            ffmpeg_path, '-y', '-i', input_path,
            '-vf', 'scale=-2:480',
            '-b:v', '800k',
            '-c:a', 'aac', '-b:a', '64k',
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_path
    except subprocess.CalledProcessError:
        st.warning("Video compression was skipped (ffmpeg not available or failed). Using original video.")
        return input_path
    except FileNotFoundError:
        st.warning("ffmpeg not found on this system. Using original video without compression.")
        return input_path


def cleanup_temp_file(path):
    """Track a temp file for later cleanup."""
    if path and path not in st.session_state.temp_files:
        st.session_state.temp_files.append(path)


def build_analysis_prompt(belt_level, favorite_moves, specific_concern):
    """Build the analysis prompt, separating system instructions from user data."""
    system_instruction = """You are a world-class Brazilian Jiu-Jitsu coach.
Analyze the provided video with high precision.
You MUST provide timestamps in "MM:SS" format and explain what happened at that moment.

【Analysis Requirements】
1. 【Positional Diagnosis (with timestamps)】:
   List the timing (MM:SS) of major positional changes (e.g., type of guard) throughout the video.
2. 【Detailed Technical Corrections】:
   Identify technical mistakes (e.g. "Hips rose at MM:SS", "Lost grip at MM:SS") with timestamps and explain the reason.
3. 【Connecting to User's Favorite Moves】:
   Specifically point out where opportunities existed to set up the user's favorite moves.
4. 【Counters and Next Steps】:
   Propose concrete transition chains: "If the opponent does X, counter with Y".
5. 【Drills for Improvement】:
   Specific practice menu/drills to overcome the mistakes in this video and level up.

Please answer in English."""

    user_context = f"""【User Profile】
- Level: {belt_level}
- Favorite Style: {favorite_moves if favorite_moves else 'Not specified'}
- Specific Focus/Concern: {specific_concern if specific_concern else 'Not specified'}"""

    return system_instruction + "\n\n" + user_context


PROCESSING_TIMEOUT_SECONDS = 300  # 5 minute timeout


# --- 4. Onboarding ---
if not api_key:
    st.info("Please enter your Gemini API Key in the sidebar to get started.")
    st.markdown("""
### How to use this app

1. **Enter your Gemini API Key** in the sidebar
2. **Upload a sparring video** or paste a YouTube URL
3. **Customize your profile** (optional) — belt level, favorite moves, focus areas
4. **Click "Analyze Video"** to receive a personalized expert coaching report
""")

# --- 5. Main Logic ---
if api_key:
    client = genai.Client(api_key=api_key)
    model_id = "gemini-2.5-pro"

    tab1, tab2 = st.tabs(["📂 Upload Video", "🔗 Analyze from YouTube URL"])

    with tab1:
        uploaded_file = st.file_uploader("Select Sparring Video", type=["mp4", "mov", "avi"])
        if uploaded_file:
            temp_dir = tempfile.mkdtemp()
            path = os.path.join(temp_dir, "upload.mp4")
            with open(path, "wb") as f:
                f.write(uploaded_file.read())
            st.session_state.video_path = path
            cleanup_temp_file(path)
            st.success("Video uploaded successfully!")

    with tab2:
        url = st.text_input("Enter YouTube URL")
        if url and st.button("Get Video"):
            with st.spinner("Downloading video from YouTube..."):
                try:
                    temp_dir = tempfile.mkdtemp()
                    yt_path = os.path.join(temp_dir, "youtube.mp4")
                    ydl_opts = {'format': 'mp4[height<=480]', 'outtmpl': yt_path, 'overwrites': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    st.session_state.video_path = yt_path
                    cleanup_temp_file(yt_path)
                    st.rerun()
                except yt_dlp.utils.DownloadError:
                    st.error("Could not download this video. Please check the URL and try again.")
                except Exception:
                    st.error("An unexpected error occurred while downloading the video. Please try a different URL.")

    # --- 6. Analysis Section ---
    if st.session_state.video_path and os.path.exists(st.session_state.video_path):
        st.video(st.session_state.video_path)

        if st.button("🚀 Analyze Video"):
            temp_dir = tempfile.mkdtemp()
            processed_path = os.path.join(temp_dir, "optimized.mp4")

            status = st.empty()
            try:
                # Phase 1: Compress
                status.info("Compressing video...")
                final_path = compress_video(st.session_state.video_path, processed_path)
                cleanup_temp_file(processed_path)

                # Phase 2: Upload
                status.info("Uploading video to Gemini...")
                uploaded_video = client.files.upload(file=final_path)

                # Phase 3: Wait for processing with timeout
                status.info("Waiting for AI to process the video...")
                elapsed = 0
                while uploaded_video.state == "PROCESSING":
                    if elapsed >= PROCESSING_TIMEOUT_SECONDS:
                        client.files.delete(name=uploaded_video.name)
                        st.error("Video processing timed out. Please try a shorter or smaller video.")
                        st.stop()
                    time.sleep(2)
                    elapsed += 2
                    uploaded_video = client.files.get(name=uploaded_video.name)

                # Phase 4: Generate analysis
                status.info("Generating personalized analysis report...")
                prompt = build_analysis_prompt(belt_level, favorite_moves, specific_concern)

                response = client.models.generate_content(
                    model=model_id,
                    contents=[prompt, uploaded_video]
                )

                status.empty()
                st.divider()
                st.subheader("📝 Personalized Expert Report")
                st.markdown(response.text)

                # Cleanup remote file
                client.files.delete(name=uploaded_video.name)

            except genai.errors.ClientError:
                status.empty()
                st.error("Invalid API key or request error. Please check your Gemini API key and try again.")
            except genai.errors.ServerError:
                status.empty()
                st.error("The Gemini API is temporarily unavailable. Please try again in a few minutes.")
            except Exception:
                status.empty()
                st.error("An unexpected error occurred during analysis. Please try again with a different video or check your API key.")
