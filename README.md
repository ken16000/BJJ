# BJJ Expert AI v2

AI-powered Brazilian Jiu-Jitsu sparring video analysis using Google Gemini 2.5 Pro.

Upload a sparring video (or paste a YouTube URL) and receive a personalized expert coaching report with timestamped positional diagnosis, technical corrections, and improvement drills.

## Prerequisites

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/download.html) installed and available in PATH
- A [Google Gemini API key](https://aistudio.google.com/apikey)

## Setup

```bash
git clone https://github.com/ken16000/BJJ.git
cd BJJ
pip install -r requirements.txt
```

## Usage

```bash
streamlit run main.py
```

1. Enter your Gemini API key in the sidebar
2. Upload a sparring video or paste a YouTube URL
3. Optionally set your belt level, favorite moves, and focus areas
4. Click "Analyze Video" to get your personalized report

## Analysis Report Includes

- **Positional Diagnosis** — Timestamped guard/position changes
- **Technical Corrections** — Mistakes with timestamps and explanations
- **Favorite Moves Opportunities** — Where you could have applied your preferred techniques
- **Counters & Transitions** — "If opponent does X, counter with Y"
- **Improvement Drills** — Practice menu tailored to your mistakes
