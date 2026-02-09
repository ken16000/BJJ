# BJJ Expert AI - Video Analysis App

## Project Overview
Streamlit web app that analyzes Brazilian Jiu-Jitsu sparring videos using Google Gemini AI. Users upload a video, identify themselves, and receive timestamped technical feedback. Includes a follow-up chat for deeper questions.

## Tech Stack
- **UI**: Streamlit 1.50
- **AI**: Google Gemini 2.0 Flash via `google-genai` SDK
- **Video**: ffmpeg (compression), yt_dlp (planned URL support)
- **Language**: Python 3

## Running the App
```bash
streamlit run main.py
```
Requires a Gemini API key entered in the sidebar at runtime.

## Architecture
Single-file app (`main.py`, ~154 lines). All logic is inline:
- Lines 1-18: Imports and session state init
- Lines 21-50: CSS styling
- Lines 52-63: Sidebar (settings, profile, clear)
- Lines 66-72: Video compression via ffmpeg subprocess
- Lines 74-131: Main panel (upload, identity input, analysis trigger)
- Lines 133-152: Chat panel (history display, follow-up questions)

## Key Patterns
- Session state keys: `video_path`, `chat_history`, `uploaded_video_obj`, `analysis_done`, `user_identity`
- Video is compressed to 480p/800kbps before uploading to Gemini
- Chat context sends only the last 5 messages to the model
- Gemini file upload uses polling loop to wait for processing

## Known Issues (from code review)
All previously identified issues have been addressed in the current code.

## Conventions
- Keep it as a single-file app unless complexity demands splitting
- Use Japanese comments where they already exist; English for new code
- All video temp files should be gitignored (already configured)
- API keys must never be hardcoded; always use runtime input or `st.secrets`
