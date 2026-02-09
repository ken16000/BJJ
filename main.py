import streamlit as st
from google import genai
import time
import os
import subprocess
import yt_dlp
import shutil
import tempfile
import re

# --- Constants ---
MAX_POLL_SECONDS = 120
MAX_CHAT_HISTORY = 50
CHAT_CONTEXT_WINDOW = 5
COMPRESS_HEIGHT = 480
COMPRESS_VIDEO_BITRATE = "800k"
COMPRESS_AUDIO_BITRATE = "64k"

# --- 1. App Config ---
st.set_page_config(page_title="BJJ Expert AI v6.7", layout="wide", page_icon="🥋")

if 'video_path' not in st.session_state: st.session_state.video_path = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'uploaded_video_obj' not in st.session_state: st.session_state.uploaded_video_obj = None
if 'analysis_done' not in st.session_state: st.session_state.analysis_done = False
if 'user_identity' not in st.session_state: st.session_state.user_identity = ""
if 'temp_files' not in st.session_state: st.session_state.temp_files = []
if 'uploaded_file_name' not in st.session_state: st.session_state.uploaded_file_name = None
if 'gemini_file_name' not in st.session_state: st.session_state.gemini_file_name = None

# --- CSS: ホワイトUI & ダーク入力エリア（白文字） ---
# NOTE: These CSS selectors target Streamlit internal elements and may break on version upgrades.
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #ffffff !important;
    }

    /* テキスト全般 */
    .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    label, [data-testid="stWidgetLabel"] p {
        color: #1a1a1a !important;
        font-family: 'Inter', sans-serif;
    }

    /* Identity入力欄: 背景を濃いグレー、文字を白、枠線を太くして視認性を最大化 */
    .stTextInput input {
        background-color: #262730 !important;
        color: #ffffff !important;
        border: 2px solid #1a1a1a !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        padding: 10px !important;
    }

    /* 右チャットパネル */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #f0f0f0 !important;
        background-color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)


# --- Helper Functions ---
def sanitize_user_input(text, max_len=100):
    """Strip to alphanumeric + basic punctuation, enforce max length."""
    cleaned = re.sub(r'[^\w\s.,!?\'-]', '', text, flags=re.UNICODE)
    return cleaned[:max_len].strip()


def cleanup_temp_files():
    """Delete temp files tracked in session state."""
    for path in st.session_state.get('temp_files', []):
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


def cleanup_gemini_file(client):
    """Delete the uploaded file from Gemini servers."""
    name = st.session_state.get('gemini_file_name')
    if name:
        try:
            client.files.delete(name=name)
        except Exception:
            pass


def compress_video(input_path, output_path):
    ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
    try:
        cmd = [
            ffmpeg_path, '-y', '-i', input_path,
            '-vf', f'scale=-2:{COMPRESS_HEIGHT}',
            '-b:v', COMPRESS_VIDEO_BITRATE,
            '-c:a', 'aac', '-b:a', COMPRESS_AUDIO_BITRATE,
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_path
    except subprocess.CalledProcessError:
        st.warning("Video compression failed — using original file.")
        return input_path
    except FileNotFoundError:
        st.warning("ffmpeg not found — using original file.")
        return input_path


def download_video_from_url(url):
    """Download a video from URL via yt_dlp to a temp file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp.close()
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': tmp.name,
        'quiet': True,
        'overwrites': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return tmp.name
    except Exception as e:
        st.error(f"Download failed: {e}")
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
        return None


# --- 2. Sidebar ---
with st.sidebar:
    st.markdown("### Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    language = st.selectbox("Language", ["Japanese", "English", "Korean", "French", "Spanish"])
    st.divider()
    st.markdown("### Profile")
    belt_level = st.selectbox("Your Belt Level", ["White", "Blue", "Purple", "Brown", "Black"])

    if st.button("Clear Session", use_container_width=True):
        cleanup_temp_files()
        if api_key:
            try:
                cleanup_gemini_file(genai.Client(api_key=api_key))
            except Exception:
                pass
        st.session_state.clear()
        st.rerun()

# --- 4. Main Interface ---
if api_key:
    client = genai.Client(api_key=api_key)
    model_id = "gemini-2.0-flash"

    col_main, col_chat = st.columns([1.3, 0.7], gap="large")

    with col_main:
        st.markdown("## Technical Analysis")
        tab1, tab2 = st.tabs(["Upload", "URL"])
        with tab1:
            up_file = st.file_uploader("Select Video", type=["mp4", "mov", "avi"], label_visibility="collapsed")
            if up_file:
                # Allow re-upload: detect new file by name
                if up_file.name != st.session_state.uploaded_file_name:
                    cleanup_temp_files()
                    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                    tmp.write(up_file.read())
                    tmp.close()
                    st.session_state.video_path = tmp.name
                    st.session_state.temp_files.append(tmp.name)
                    st.session_state.uploaded_file_name = up_file.name
                    st.session_state.analysis_done = False
                    st.session_state.chat_history = []
                    st.session_state.uploaded_video_obj = None
                    st.session_state.gemini_file_name = None

        with tab2:
            video_url = st.text_input("YouTube / Video URL", placeholder="https://www.youtube.com/watch?v=...")
            if st.button("Download Video"):
                if video_url:
                    with st.spinner("Downloading video..."):
                        downloaded = download_video_from_url(video_url)
                    if downloaded:
                        cleanup_temp_files()
                        st.session_state.video_path = downloaded
                        st.session_state.temp_files.append(downloaded)
                        st.session_state.uploaded_file_name = video_url
                        st.session_state.analysis_done = False
                        st.session_state.chat_history = []
                        st.session_state.uploaded_video_obj = None
                        st.session_state.gemini_file_name = None
                        st.rerun()
                else:
                    st.warning("Please enter a URL.")

        if st.session_state.video_path:
            st.video(st.session_state.video_path)

            # Identity入力欄 (視認性改善済み)
            st.session_state.user_identity = st.text_input(
                "Identify yourself (Focus of coaching):",
                value=st.session_state.user_identity,
                placeholder="e.g., The one in the White Gi"
            )

            if not st.session_state.analysis_done:
                if st.button("Run Technical Evaluation", type="primary", use_container_width=True):
                    if st.session_state.user_identity:
                        with st.status("Evaluating biomechanics...", expanded=True):
                            try:
                                tmp_compressed = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                                tmp_compressed.close()
                                st.session_state.temp_files.append(tmp_compressed.name)
                                final_v = compress_video(st.session_state.video_path, tmp_compressed.name)
                                uploaded_v = client.files.upload(file=final_v)

                                # Poll with timeout
                                start_time = time.time()
                                while uploaded_v.state == "PROCESSING":
                                    if time.time() - start_time > MAX_POLL_SECONDS:
                                        st.error("Video processing timed out. Please try again.")
                                        st.stop()
                                    time.sleep(2)
                                    uploaded_v = client.files.get(name=uploaded_v.name)

                                st.session_state.uploaded_video_obj = uploaded_v
                                st.session_state.gemini_file_name = uploaded_v.name

                                safe_identity = sanitize_user_input(st.session_state.user_identity)
                                # プロンプトの純粋技術化
                                prompt = f"""
                                You are a high-level Brazilian Jiu-Jitsu technical analyst.
                                TARGET: Provide advice ONLY for the person identified as: [{safe_identity}].
                                Language: {language}. Belt: {belt_level}.

                                ANALYSIS CORE:
                                - [MM:SS] format for every key point.
                                - GOOD: Identify mechanical advantage (Base, Leverage, Framing). Suggest the next logical transition.
                                - BAD: Explain structural failure. Recommend specific techniques/moves to fix or escape.
                                - TECHNIQUE NAMES: Use standard BJJ terminology (e.g., De La Riva, X-Guard, Underhook, Hip Escape).

                                Be direct, analytical, and focus on maximizing physical efficiency.
                                """
                                response = client.models.generate_content(model=model_id, contents=[prompt, uploaded_v])
                                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                                st.session_state.analysis_done = True
                                st.rerun()
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                    else:
                        st.warning("Please identify which player you are.")

    with col_chat:
        st.markdown('### Technical Feedback')
        with st.container(border=True):
            chat_box = st.container(height=650, border=False)
            with chat_box:
                if not st.session_state.chat_history: st.write("Awaiting analysis...")
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            if not st.session_state.analysis_done:
                st.warning("Run an analysis first to enable the chat.")
            elif not st.session_state.user_identity:
                st.warning("Please identify yourself before chatting.")
            else:
                st.caption(f"Chat uses the last {CHAT_CONTEXT_WINDOW} messages for context.")
                if user_input := st.chat_input("Ask about details..."):
                    if st.session_state.uploaded_video_obj:
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        # Cap chat history
                        if len(st.session_state.chat_history) > MAX_CHAT_HISTORY:
                            st.session_state.chat_history = st.session_state.chat_history[-MAX_CHAT_HISTORY:]

                        safe_identity = sanitize_user_input(st.session_state.user_identity)
                        contents = [st.session_state.uploaded_video_obj]
                        contents.append(f"Focus advice on [{safe_identity}]. Be technically precise.\n---\nConversation history:")
                        for m in st.session_state.chat_history[-CHAT_CONTEXT_WINDOW:]:
                            contents.append(f"{m['role']}: {m['content']}")
                        try:
                            with st.spinner("Thinking..."):
                                res = client.models.generate_content(model=model_id, contents=contents)
                            st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Chat response failed: {e}")
else:
    st.info("Please enter your API Key in the sidebar.")
