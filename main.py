import streamlit as st
from google import genai
import time
import os
import subprocess
import yt_dlp

# --- 1. App Config ---
st.set_page_config(page_title="BJJ Expert AI v2", layout="wide", page_icon="🥋")

if 'video_path' not in st.session_state:
    st.session_state.video_path = None

st.title("🥋 BJJ Advanced Technical Analysis (Gemini 2.5 Pro)")

# --- 2. Sidebar (Personalization) ---
with st.sidebar:
    st.header("⚙️ Settings & Profile")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    st.subheader("👤 Your Style")
    # Hints for AI
    belt_level = st.selectbox("Current Belt Level", ["White", "Blue", "Purple", "Brown", "Black"])
    favorite_moves = st.text_input("Favorite Guards/Moves", placeholder="e.g. De La Riva, Spider Guard, Triangle Choke")
    specific_concern = st.text_area("Specific Concerns / Focus Area", placeholder="e.g. framing against pass guard, timing for shrimp")
    
    st.divider()
    if st.button("Clear Cache (Video Data)"):
        st.session_state.video_path = None
        st.rerun()

# --- 3. Video Compression Function ---
def compress_video(input_path, output_path):
    # Consider Anaconda environment path
    possible_ffmpeg_paths = ["/Users/kenichirokenichirououchioouchi/opt/anaconda3/bin/ffmpeg", "ffmpeg"]
    ffmpeg_path = next((p for p in possible_ffmpeg_paths if os.path.exists(p) or p == "ffmpeg"), "ffmpeg")

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
    except Exception as e:
        st.warning(f"ffmpeg compression failed. Sending original video size.")
        return input_path

# --- 4. Main Logic ---
if api_key:
    client = genai.Client(api_key=api_key)
    # Specify the latest model from the list
    model_id = "gemini-2.5-pro" 

    tab1, tab2 = st.tabs(["📂 Upload Video", "🔗 Analyze from YouTube URL"])

    with tab1:
        uploaded_file = st.file_uploader("Select Sparring Video", type=["mp4", "mov", "avi"])
        if uploaded_file:
            path = "temp_raw.mp4"
            with open(path, "wb") as f:
                f.write(uploaded_file.read())
            st.session_state.video_path = path

    with tab2:
        url = st.text_input("Enter YouTube URL")
        if url and st.button("Get Video"):
            with st.spinner("Downloading..."):
                try:
                    yt_path = "temp_yt.mp4"
                    ydl_opts = {'format': 'mp4[height<=480]', 'outtmpl': yt_path, 'overwrites': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    st.session_state.video_path = yt_path
                    st.rerun() 
                except Exception as e:
                    st.error(f"YouTube Download Error: {e}")

    # --- 5. Analysis Section ---
    if st.session_state.video_path and os.path.exists(st.session_state.video_path):
        st.video(st.session_state.video_path)
        
        if st.button("🚀 Start Latest AI Analysis"):
            processed_path = "optimized_for_ai.mp4"
            final_path = compress_video(st.session_state.video_path, processed_path)
            
            with st.spinner("Latest AI is analyzing the video..."):
                try:
                    # Upload file and wait for status
                    uploaded_video = client.files.upload(file=final_path)
                    while uploaded_video.state == "PROCESSING":
                        time.sleep(2)
                        uploaded_video = client.files.get(name=uploaded_video.name)

                    # Build personalized prompt
                    prompt = f"""
                    You are a world-class Brazilian Jiu-Jitsu coach.
                    Analyze the provided video with high precision, considering the following user information.
                    You MUST provide timestamps in "MM:SS" format and explain what happened at that moment.

                    【User Profile】
                    - Level: {belt_level}
                    - Favorite Style: {favorite_moves}
                    - Specific Focus/Concern: {specific_concern}

                    【Analysis Requirements】
                    1. 【Positional Diagnosis (with timestamps)】:
                       List the timing (MM:SS) of major positional changes (e.g., type of guard) throughout the video.
                    2. 【Detailed Technical Corrections】:
                       Identify technical mistakes (e.g. "Hips rose at MM:SS", "Lost grip at MM:SS") with timestamps and explain the reason.
                    3. 【Connecting to Your Favorite Moves】:
                       Specifically point out where opportunities existed to set up the user's favorite moves ("{favorite_moves}").
                    4. 【Counters and Next Steps】:
                       Propose concrete transition chains: "If the opponent does X, counter with Y".
                    5. 【Drills for Improvement】:
                       Specific practice menu/drills to overcome the mistakes in this video and level up.
                    
                    Please answer in English.
                    """
                    
                    response = client.models.generate_content(
                        model=model_id,
                        contents=[prompt, uploaded_video]
                    )

                    st.divider()
                    st.subheader("📝 Personalized Expert Report")
                    st.markdown(response.text)
                    
                    # Delete file on server
                    client.files.delete(name=uploaded_video.name)
                    
                except Exception as e:
                    st.error(f"Analysis Error: {e}")
else:
    st.info("Please enter your Gemini API Key in the sidebar.")
