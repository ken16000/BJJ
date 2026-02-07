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

# --- 3. Video Compression & Captioning Functions ---
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

def parse_timestamp(ts_str):
    """Converts MM:SS to total seconds."""
    try:
        parts = ts_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return 0
    return 0

def generate_srt(captions, srt_path):
    """Generates an SRT file from the captions list."""
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, cap in enumerate(captions):
            start_seconds = parse_timestamp(cap['timestamp'])
            end_seconds = start_seconds + 4  # Show caption for 4 seconds
            
            # Format: 00:00:00,000
            start_ts = f"{start_seconds // 3600:02}:{(start_seconds % 3600) // 60:02}:{start_seconds % 60:02},000"
            end_ts = f"{end_seconds // 3600:02}:{(end_seconds % 3600) // 60:02}:{end_seconds % 60:02},000"
            
            f.write(f"{i+1}\n")
            f.write(f"{start_ts} --> {end_ts}\n")
            f.write(f"{cap['text']}\n\n")

def burn_subtitles(video_path, srt_path, output_path):
    """Burns subtitles into the video using ffmpeg."""
    # Consider Anaconda environment path
    possible_ffmpeg_paths = ["/Users/kenichirokenichirououchioouchi/opt/anaconda3/bin/ffmpeg", "ffmpeg"]
    ffmpeg_path = next((p for p in possible_ffmpeg_paths if os.path.exists(p) or p == "ffmpeg"), "ffmpeg")
    
    try:
        # Note: 'subtitles' filter requires the full path to the SRT file
        abs_srt_path = os.path.abspath(srt_path).replace('\\', '/')
        # Escape colon in path for ffmpeg filter (Windows mainly, but safe practice)
        abs_srt_path = abs_srt_path.replace(':', '\\:')
        
        cmd = [
            ffmpeg_path, '-y', '-i', video_path,
            '-vf', f"subtitles='{abs_srt_path}':force_style='FontSize=24,PrimaryColour=&H00FFFF,BackColour=&H80000000,BorderStyle=3'",
            '-c:a', 'copy',
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_path
    except Exception as e:
        print(f"Error burning subtitles: {e}")
        return None

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
                    
                    【User Profile】
                    - Level: {belt_level}
                    - Favorite Style: {favorite_moves}
                    - Specific Focus/Concern: {specific_concern}

                    【Output Format】
                    You must output a valid JSON object with the following structure:
                    {{
                        "captions": [
                            {{
                                "timestamp": "MM:SS",
                                "text": "Short, punchy critique or advice (max 15 words) to be displayed on video."
                            }}
                        ],
                        "detailed_report": "Full markdown report containing 1. Positional Diagnosis, 2. Detailed Technical Corrections, 3. Connecting to Favorite Moves, 4. Counters and Next Steps, 5. Drills for Improvement."
                    }}
                    
                    Ensure the "captions" are sorted by timestamp.
                    """
                    
                    response = client.models.generate_content(
                        model=model_id,
                        contents=[prompt, uploaded_video],
                        config={'response_mime_type':'application/json'}
                    )
                    
                    # Parse JSON response
                    try:
                        import json
                        analysis_data = json.loads(response.text)
                        captions = analysis_data.get("captions", [])
                        detailed_report = analysis_data.get("detailed_report", "No report generated.")
                    except json.JSONDecodeError:
                        st.error("Failed to parse AI response as JSON.")
                        st.text(response.text)
                        st.stop()

                    st.divider()
                    st.subheader("📝 Personalized Expert Report")
                    st.markdown(detailed_report)
                    
                    # Generate Caption Video
                    if captions:
                        with st.status("🎬 Generating Captioned Video...", expanded=True) as status:
                            srt_path = "subtitles.srt"
                            captioned_video_path = "captioned_output.mp4"
                            
                            st.write("Generating subtitles...")
                            generate_srt(captions, srt_path)
                            
                            st.write("Burning subtitles into video...")
                            result_path = burn_subtitles(final_path, srt_path, captioned_video_path)
                            
                            if result_path and os.path.exists(result_path):
                                st.success("Video generated!")
                                st.video(result_path)
                                st.session_state.captioned_video_path = result_path
                            else:
                                st.error("Failed to generate captioned video.")
                            status.update(label="Analysis Complete!", state="complete", expanded=False)

                    # Delete file on server
                    client.files.delete(name=uploaded_video.name)
                    
                except Exception as e:
                    st.error(f"Analysis Error: {e}")
                    import traceback
                    st.text(traceback.format_exc())
else:
    st.info("Please enter your Gemini API Key in the sidebar.")