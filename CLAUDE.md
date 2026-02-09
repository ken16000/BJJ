# CLAUDE.md

## Project Overview

BJJ Expert AI v2 — A Streamlit web application that provides personalized Brazilian Jiu-Jitsu (BJJ) sparring video analysis powered by Google Gemini 2.5 Pro.

## Business Requirements

### Core Purpose

Enable BJJ practitioners to upload sparring videos and receive AI-generated expert coaching feedback tailored to their skill level and personal style.

### Target Users

BJJ practitioners of all levels (White through Black belt) who want to review and improve their sparring technique through AI-powered video analysis.

### Key Features

#### 1. User Profile & Personalization
- Users select their current belt level (White, Blue, Purple, Brown, Black)
- Users input their favorite guards/moves (e.g., De La Riva, Spider Guard, Triangle Choke)
- Users describe specific concerns or focus areas (e.g., framing against guard pass, timing for shrimp)
- All analysis output is personalized based on these inputs

#### 2. Video Input (Two Methods)
- **File Upload**: Users can upload sparring videos directly (MP4, MOV, AVI)
- **YouTube URL**: Users can paste a YouTube URL to download and analyze a video

#### 3. Video Compression
- Videos are automatically compressed (scaled to 480p, 800k video bitrate) via ffmpeg before sending to the AI
- If compression fails, the original video is sent as a fallback

#### 4. AI-Powered Analysis Report
The AI generates a personalized expert report with 5 sections:
1. **Positional Diagnosis** — Timestamps (MM:SS) of major positional changes (guard types, transitions)
2. **Detailed Technical Corrections** — Specific mistakes identified with timestamps and explanations
3. **Connecting to Favorite Moves** — Opportunities where the user could have applied their preferred techniques
4. **Counters and Next Steps** — Concrete transition chains ("If opponent does X, counter with Y")
5. **Drills for Improvement** — Practice menu to address mistakes found in the video

#### 5. Cache Management
- Users can clear the loaded video data to start a new analysis session

### Authentication
- Users provide their own Google Gemini API key via the sidebar
- No built-in user accounts or authentication system

## Tech Stack

- **Language**: Python 3
- **UI Framework**: Streamlit
- **AI Model**: Google Gemini 2.5 Pro (via `google-genai` SDK)
- **Video Download**: yt-dlp (for YouTube URLs)
- **Video Compression**: ffmpeg (via subprocess)

## How to Run

```bash
pip install streamlit google-genai yt-dlp
streamlit run main.py
```

### Prerequisites
- Python 3
- ffmpeg installed and available in PATH
- A valid Google Gemini API key

## Code Structure

Single-file application (`main.py`, ~141 lines):
- Lines 1-6: Imports
- Lines 8-14: App config and session state
- Lines 16-31: Sidebar (API key, user profile, cache clear)
- Lines 33-51: Video compression function
- Lines 53-82: Main logic — video input tabs (upload & YouTube)
- Lines 83-138: Analysis section — video preview, AI analysis, report output

## Git

- Write commit messages in English
- Keep commits focused and atomic
