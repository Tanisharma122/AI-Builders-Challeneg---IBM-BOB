# CreaTect AI — Agentic Content Orchestration Platform

> **IBM AI Builders Challenge** · Powered by IBM Granite 3.0 · Faster-Whisper · FFmpeg · FLUX.1 · Gemini

One platform to accelerate your ideation, production, and distribution by 80%. AI video clipping, text-to-image B-roll generation, and content-aware thumbnail creation — all in one dark-themed, creator-first interface.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [YouTube Publishing Flow](#youtube-publishing-flow)
- [Screenshots](#screenshots)

---

## Overview

CreaTect AI is a full-stack agentic content platform that takes long-form video and turns it into platform-ready viral content in three steps:

1. **Upload & Transcribe** — Upload a local video or paste a YouTube URL. Faster-Whisper produces word-level timestamps.
2. **Analyze & Script** — IBM Granite 3.0 identifies the top 5 viral segments, scores virality (0–100), and generates hook text + script commentary.
3. **Render & Distribute** — FFmpeg crops to 9:16, burns in karaoke captions, and publishes directly to YouTube Shorts via OAuth 2.0.

Additionally:
- **Text-to-Image** — Generate high-resolution B-roll assets from a text prompt using Gemini prompt enhancement + FLUX.1-schnell.
- **AI Thumbnail Generator** — Enter a video title, choose style/mood, and get a scroll-stopping YouTube thumbnail in seconds.

---

## Features

| Feature | Description |
|---|---|
| 🎬 **AI Video Clipping** | Word-level transcription → IBM Granite viral analysis → 9:16 FFmpeg rendering |
| ▶ **YouTube Shorts Publishing** | One-click OAuth 2.0 publish with chunked resumable upload |
| 🤖 **AI Title & Tag Suggestions** | Heuristic + Granite-powered title, description, and viral tag generation |
| ↓ **Download Clips** | Download any rendered clip directly from the studio |
| 🖼 **Text-to-Image** | Gemini-enhanced prompts → FLUX.1-schnell via HuggingFace Router |
| 🎨 **Thumbnail Generator** | Gemini scene synthesis → FLUX.1-schnell with smart text overlay placement |
| 🌑 **Dark UI** | Full dark theme with brand color system (oklch-based, Tailwind v4) |

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111 + Uvicorn |
| Transcription | Faster-Whisper 1.0.3 (word-level timestamps) |
| LLM Analysis | IBM Granite 3.0 via HuggingFace Inference API |
| Video Processing | FFmpeg + ffmpeg-python |
| Speaker Diarization | Pyannote.audio 3.3.2 |
| YouTube API | google-api-python-client + google-auth-oauthlib |
| Configuration | pydantic-settings |

### Frontend
| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router, Turbopack) |
| Language | TypeScript 5 |
| Styling | Tailwind CSS v4 + tw-animate-css |
| UI Components | shadcn/ui + @base-ui/react |
| Image Generation | FLUX.1-schnell via HuggingFace Router |
| Prompt Enhancement | Gemini 2.0 Flash / 2.5 Flash |
| Icons | lucide-react |

---

## Project Structure

```
project-root/
├── backend/                          # FastAPI Python backend
│   ├── app/
│   │   ├── main.py                   # App factory, CORS, router registration
│   │   ├── config.py                 # pydantic-settings env config
│   │   ├── api/routes/
│   │   │   ├── video.py              # /api/video/* (transcribe, analyze, process, status)
│   │   │   ├── youtube_auth.py       # /api/auth/youtube/* (OAuth login + callback)
│   │   │   └── publish.py            # /api/publish/youtube (upload + suggestions)
│   │   ├── services/
│   │   │   ├── transcription_service.py   # Faster-Whisper integration
│   │   │   ├── granite_analyzer.py        # IBM Granite 3.0 LLM + JSON validation
│   │   │   ├── video_processor.py         # FFmpeg 9:16 crop pipeline
│   │   │   ├── subtitle_service.py        # .srt karaoke caption generation
│   │   │   ├── youtube_service.py         # yt-dlp YouTube download
│   │   │   └── youtube_publisher.py       # YouTube Data API v3 upload + suggestions
│   │   ├── models/                    # Pydantic models (transcript, job, granite output)
│   │   ├── schemas/                   # JSON Schema for Granite output validation
│   │   └── utils/                     # FFmpeg utils, file utils
│   ├── tests/                         # pytest test suite
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                          # Next.js unified frontend
│   ├── app/
│   │   ├── page.tsx                   # Landing page (CreaTect AI home)
│   │   ├── studio-upload/             # Video upload form
│   │   ├── studio/[jobId]/            # Video clipping studio
│   │   ├── auth/youtube/callback/     # OAuth callback page
│   │   ├── features/
│   │   │   ├── video-clipping/        # Feature showcase → studio
│   │   │   ├── text-to-image/         # Text-to-image workspace
│   │   │   └── thumbnail-generator/   # Thumbnail generator workspace
│   │   └── api/
│   │       ├── generate-image/        # FLUX.1 image generation route
│   │       ├── enhance-prompt/        # Gemini prompt enhancement route
│   │       └── generate-thumbnail/    # Gemini + FLUX thumbnail route
│   ├── components/
│   │   ├── home/                      # Landing page sections (Hero, Pricing, etc.)
│   │   ├── features/                  # Feature workspaces + feature-section
│   │   ├── studio/                    # VideoPreviewPlayer, ClipTimeline, etc.
│   │   ├── upload/                    # VideoUploader, ProcessingProgress
│   │   ├── shared/                    # ScoreGauge SVG component
│   │   ├── site-nav.tsx               # Sticky dark navigation
│   │   ├── site-footer.tsx            # Footer with product links
│   │   └── feature-submenu.tsx        # Sub-nav across feature pages
│   ├── lib/
│   │   ├── api.ts                     # Typed fetch wrappers for all backend endpoints
│   │   └── types.ts                   # TypeScript interfaces (mirrors Pydantic models)
│   ├── hooks/
│   │   └── useJobPolling.ts           # SSE/polling hook for job status
│   └── next.config.ts                 # Proxy /api/* → FastAPI :8000
│
└── tasks.md                           # Implementation plan & spec
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- FFmpeg installed and on PATH
- HuggingFace account (free tier works)
- Google Cloud project with YouTube Data API v3 enabled

### 1. Clone the repository
```bash
git clone https://github.com/Tanisharma122/AI-Builders-Challeneg---IBM-BOB.git
cd AI-Builders-Challeneg---IBM-BOB
```

### 2. Backend setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Fill in your values in .env (see Environment Variables section)
```

### 3. Frontend setup
```bash
cd frontend
npm install
# .env.local is already configured for local development
```

### 4. Run both servers (two terminals)

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Open the app
```
http://localhost:3000
```

---

## Environment Variables

### `backend/.env`
```env
# HuggingFace
HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxx        # For IBM Granite 3.0 inference
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx          # For Pyannote gated model

# Whisper
WHISPER_MODEL_SIZE=base                   # tiny | base | small | medium | large-v3

# File storage
UPLOAD_DIR=C:/tmp/videoclip/uploads
OUTPUT_DIR=C:/tmp/videoclip/outputs

# FFmpeg
FFMPEG_PATH=ffmpeg                        # or absolute path
FFMPEG_TIMEOUT=120

# LLM (set USE_OLLAMA=true for local Ollama instead of HuggingFace)
USE_OLLAMA=false
OLLAMA_BASE_URL=http://localhost:11434

# YouTube OAuth 2.0
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REDIRECT_URI=http://localhost:3000/auth/youtube/callback

# CORS
CORS_ORIGINS=["http://localhost:3000"]
MAX_UPLOAD_SIZE_MB=500
```

### `frontend/.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000

# For text-to-image and thumbnail generator
GEMINI_API_KEY=your_gemini_api_key
GEMINI_API_KEY_2=your_gemini_api_key_backup
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
```

---

## API Reference

### Video Pipeline
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/video/transcribe` | Upload file or YouTube URL → start transcription job |
| `POST` | `/api/video/analyze` | Trigger IBM Granite viral analysis |
| `POST` | `/api/video/process` | Render 9:16 clips with FFmpeg |
| `GET` | `/api/video/status/{job_id}` | Poll job status + progress |
| `GET` | `/api/video/analysis/{job_id}` | Fetch Granite analysis JSON |

### YouTube Publishing
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/auth/youtube/login` | Get Google OAuth consent URL |
| `GET` | `/api/auth/youtube/callback` | Exchange auth code for tokens |
| `POST` | `/api/publish/youtube` | Upload clip to YouTube Shorts |
| `POST` | `/api/publish/youtube/suggest` | Generate titles, descriptions, viral tags |

### Next.js API Routes (frontend)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/enhance-prompt` | Gemini prompt enhancement for image gen |
| `POST` | `/api/generate-image` | FLUX.1-schnell image generation |
| `POST` | `/api/generate-thumbnail` | Gemini + FLUX thumbnail generation |

---

## YouTube Publishing Flow

1. Click **"Publish to YouTube Shorts"** in the studio
2. Click **"Sign in with Google"** — a popup opens to Google consent screen
3. After granting permission → popup closes, AI suggestions load automatically
4. Pick from **5 AI-generated title chips**, **3 description suggestions**, **30 viral tags**
5. Click **"Publish to YouTube Shorts"** — chunked resumable upload begins
6. Live Shorts URL appears: `https://youtube.com/shorts/{video_id}`

### Google Cloud Setup (one-time)
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create project → Enable **YouTube Data API v3**
3. OAuth 2.0 Credentials → Web application
4. Add Authorised redirect URI: `http://localhost:3000/auth/youtube/callback`
5. Add your Google account as a **Test User** (OAuth consent screen)

---

## Screenshots

> Studio — Video preview, clip timeline, Granite inspector, and YouTube publish button
> Landing — Full CreaTect AI dark-themed marketing page
> Text-to-Image — Prompt → Gemini enhancement → FLUX.1 generation workspace
> Thumbnail Generator — Title + mood → AI-generated YouTube thumbnail

---

## License

MIT — Built for the IBM AI Builders Challenge.

---

*Made with ❤️ using IBM Bob · IBM Granite 3.0 · Faster-Whisper · FFmpeg · FLUX.1*
