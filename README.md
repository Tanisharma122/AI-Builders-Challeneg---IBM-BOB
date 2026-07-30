# Tani â€” Agentic Content Orchestration Platform

<div align="center">

![Tani](https://img.shields.io/badge/Tani%20AI-Agentic%20Content%20Platform-blue?style=for-the-badge)
![IBM Bob](https://img.shields.io/badge/Built%20with-IBM%20Bob-0f62fe?style=for-the-badge&logo=ibm)
![IBM Granite](https://img.shields.io/badge/Powered%20by-IBM%20Granite%203.0-0f62fe?style=for-the-badge&logo=ibm)
![Challenge](https://img.shields.io/badge/IBM%20AI%20Builders-Challenge%202025-purple?style=for-the-badge)

**One platform to accelerate your content ideation, production, and distribution by 80%.**

</div>

---

## ðŸ† IBM AI Builders Challenge â€” Submission

| Field | Details |
|---|---|
| **Challenge Theme** | Agentic AI for Content Creation & Distribution |
| **Primary IBM Tool** | **IBM Bob** (AI Software Engineer) |
| **IBM AI Model** | **IBM Granite 3.0** (`ibm-granite/granite-3.0-8b-instruct`) |
| **IBM Platform** | **IBM watsonx.ai** â€” Granite inference via HuggingFace |
| **Team** | Tanisha Sharma · Jeneesh Vandra |

---

## ðŸš¨ Problem Statement

Content creators face a **brutal production bottleneck**:

- A single 1-hour podcast or interview contains **dozens of viral moments** â€” but identifying them manually takes 4â€“8 hours of editing work.
- After clipping, creators must still **write titles, descriptions, hashtags**, generate **thumbnails**, create **B-roll visuals**, and **distribute** across 5+ platforms.
- Most AI tools solve **one** part of this workflow â€” forcing creators to juggle 6+ disconnected apps.
- **80% of creator time** is spent on repetitive post-production instead of making content.

> **Result:** Great content never gets made because the production pipeline is too slow and expensive.

---

## ðŸ’¡ Solution Description

**Tani** is a fully integrated, AI-orchestrated content platform that takes a raw long-form video and **autonomously handles every stage** of the creator workflow:

```
Raw Video â†’ Transcription â†’ Viral Analysis â†’ 9:16 Clip Rendering
         â†’ Metadata Generation â†’ YouTube Publishing â†’ Done
```

Additionally:
- **Text-to-Image**: Generate B-roll visuals from a text prompt in seconds
- **AI Thumbnail Generator**: Create scroll-stopping YouTube thumbnails with one click

Everything lives in **one unified dark-themed platform** â€” no switching between tools.

---

## ðŸ¤– AI Approach & Architecture

### System Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                        FRONTEND (Next.js 16)                     â”‚
â”‚  Landing Page â†’ Upload Studio â†’ Video Studio â†’ Feature Pages    â”‚
â”‚  Text-to-Image Workspace â”‚ Thumbnail Generator â”‚ YouTube Publish â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                               â”‚ HTTP / REST
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                       BACKEND (FastAPI)                          â”‚
â”‚                                                                  â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚  â”‚  Faster-    â”‚  â”‚  IBM Granite â”‚  â”‚   FFmpeg Pipeline        â”‚ â”‚
â”‚  â”‚  Whisper    â”‚  â”‚  3.0 via     â”‚  â”‚   9:16 Crop + Subtitles  â”‚ â”‚
â”‚  â”‚  Transcribe â”‚  â”‚  watsonx.ai  â”‚  â”‚   + Karaoke Captions     â”‚ â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â”‚         â”‚                â”‚                      â”‚                â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚  â”‚ Word-level  â”‚  â”‚ Viral Segmentâ”‚  â”‚  YouTube Data API v3     â”‚ â”‚
â”‚  â”‚ Timestamps  â”‚  â”‚ Scoring 0-100â”‚  â”‚  OAuth 2.0 Publishing    â”‚ â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                               â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    EXTERNAL AI SERVICES                          â”‚
â”‚  IBM Granite 3.0 (HuggingFace)  â”‚  FLUX.1-schnell (HF Router)  â”‚
â”‚  Gemini 2.5 Flash (Prompt Eng)  â”‚  Pyannote Speaker Diarization â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### AI Pipeline â€” Step by Step

| Step | Technology | What Happens |
|---|---|---|
| **1. Ingest** | `yt-dlp` / File Upload | Download YouTube video or accept upload (up to 500MB) |
| **2. Transcribe** | **Faster-Whisper** | Word-level timestamps with speaker detection |
| **3. Analyze** | **IBM Granite 3.0** | LLM identifies top 5 viral segments, scores 0â€“100, generates hook text + script commentary |
| **4. Validate** | `jsonschema` | Granite output validated against strict JSON Schema |
| **5. Diarize** | **Pyannote.audio** | Speaker tracking for smart 9:16 crop positioning |
| **6. Render** | **FFmpeg** | Trim + 9:16 crop + subtitle burn-in with karaoke timing |
| **7. Suggest** | **IBM Granite** heuristics | Generate viral titles, descriptions, 30 hashtags |
| **8. Publish** | **YouTube Data API v3** | Chunked resumable OAuth 2.0 upload â†’ live Shorts URL |

### IBM Granite 3.0 â€” Viral Analysis Prompt Strategy

IBM Granite 3.0 (`ibm-granite/granite-3.0-8b-instruct`) is the **core intelligence** of Tani:

- Receives the full word-level transcript as structured JSON
- Returns **exactly 5 viral clips** with: `start_time`, `end_time`, `hook_text`, `script_commentary`, `virality_score` (0â€“100), `virality_reasoning`
- Strict **JSON-only output** â€” no markdown, no prose
- Output validated with `jsonschema` â†’ retry with stricter prompt on failure
- `tenacity` exponential backoff for HuggingFace rate limits (3 attempts)
- Fallback to **local Ollama** via `USE_OLLAMA=true` config flag

---

## ðŸ”µ IBM Tools â€” Detailed Usage

### 1. ðŸ¤– IBM Bob (AI Software Engineer)

> **IBM Bob is the AI software engineer that built this entire project.**

**IBM Bob** (`bob.ibm.com`) was used as the **primary development tool** throughout the entire project lifecycle:

#### What IBM Bob Built:
- âœ… **Complete FastAPI backend** â€” all 8 service modules, 3 API route files, Pydantic models, JSON schemas, pytest test suite
- âœ… **Full Next.js frontend** â€” landing page, video studio, text-to-image workspace, thumbnail generator, all 50+ React components
- âœ… **YouTube OAuth 2.0 flow** â€” complete Google OAuth integration with popup window, token exchange, chunked resumable upload
- âœ… **IBM Granite integration** â€” prompt engineering, JSON schema validation, retry logic with tenacity
- âœ… **FFmpeg pipeline** â€” 9:16 smart crop, subtitle burn-in, speaker-aware framing with Pyannote
- âœ… **UI/UX integration** â€” merged UI-1 design system with functional backend, dark theme, all color tokens
- âœ… **Bug fixes** â€” resolved `httplib2` Windows redirect bug, Next.js Server/Client component split, dark theme visibility issues
- âœ… **Git & deployment** â€” `.gitignore`, secrets audit, README, GitHub push

#### IBM Bob's Development Approach:
IBM Bob followed a **spec-driven, sequential implementation** plan (`tasks.md`) with:
- Modular service architecture (each service is independently testable)
- Type-safe TypeScript interfaces mirroring Pydantic models exactly
- Clean error handling at every layer (HTTP status codes, typed exceptions)
- Zero TypeScript errors (`npx tsc --noEmit` passes clean)

---

### 2. ðŸ”µ IBM Granite 3.0

**Model:** `ibm-granite/granite-3.0-8b-instruct` via **IBM watsonx.ai / HuggingFace Inference API**

**Role:** Core viral intelligence engine

```python
# How IBM Granite 3.0 is used in Tani
from huggingface_hub import InferenceClient

client = InferenceClient(model="ibm-granite/granite-3.0-8b-instruct")

# Granite receives the full transcript and returns structured viral clips
response = client.text_generation(
    prompt=_build_prompt(transcript),  # system + user prompt
    max_new_tokens=2048,
    temperature=0.2,                   # low temp for consistent JSON
)
# Output: {"clips": [{rank, start_time, end_time, hook_text, virality_score, ...}]}
```

**Granite handles:**
- Identifying the most engaging 30-60 second segments
- Scoring emotional impact and virality potential (0â€“100)
- Writing the "hook" â€” the opening line that makes viewers stop scrolling
- Explaining *why* each segment will go viral

---

## ðŸŽ¯ Selected Challenge Theme

> **"Agentic AI for Creators"** â€” Building AI agents that autonomously handle multi-step creative workflows, reducing human effort from hours to seconds.

Tani demonstrates agentic behavior through:

1. **Multi-step autonomy** â€” The pipeline runs from raw video â†’ live YouTube URL with minimal human input
2. **Tool use** â€” The system orchestrates Whisper, Granite, FFmpeg, Pyannote, and YouTube API as specialized tools
3. **Self-validation** â€” Granite output is validated; on failure, the agent retries with a stricter prompt
4. **Adaptive routing** â€” Falls back to local Ollama if cloud API is unavailable
5. **Cross-platform distribution** â€” One clip, exported for YouTube Shorts, Instagram Reels, LinkedIn, and X

---

## âœ¨ Features

| Feature | Description |
|---|---|
| ðŸŽ¬ **AI Video Clipping** | Word-level transcription â†’ IBM Granite viral analysis â†’ 9:16 FFmpeg rendering with karaoke captions |
| â–¶ **YouTube Shorts Publishing** | One-click Google OAuth 2.0 publish with chunked resumable upload (no httplib2 bugs) |
| ðŸ¤– **AI Metadata Generation** | IBM Granite-powered title suggestions, 3 description variants, 30 viral hashtags |
| â†“ **Download Clips** | Download any rendered clip directly from the studio |
| ðŸ–¼ **Text-to-Image** | Gemini-enhanced prompts â†’ FLUX.1-schnell via HuggingFace Router |
| ðŸŽ¨ **Thumbnail Generator** | Gemini scene synthesis â†’ FLUX.1-schnell with smart text overlay placement |
| ðŸŒ‘ **Full Dark UI** | Tani dark theme with brand color system â€” every page, every component |
| ðŸ“± **Multi-Platform Export** | YouTube Shorts, Instagram Reels, LinkedIn, X â€” platform-specific metadata |

---

## ðŸ— Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | **FastAPI 0.111** + Uvicorn |
| **IBM AI** | **IBM Granite 3.0** via HuggingFace / watsonx.ai |
| Transcription | **Faster-Whisper 1.0.3** (word-level timestamps) |
| Video Processing | **FFmpeg** + ffmpeg-python |
| Speaker Diarization | **Pyannote.audio 3.3.2** |
| YouTube API | google-api-python-client + google-auth-oauthlib |
| YouTube Download | yt-dlp |
| Retry Logic | tenacity (exponential backoff) |
| Config | pydantic-settings |

### Frontend
| Layer | Technology |
|---|---|
| Framework | **Next.js 16** (App Router, Turbopack) |
| Language | TypeScript 5 |
| Styling | **Tailwind CSS v4** + tw-animate-css |
| UI Components | shadcn/ui + @base-ui/react |
| Image Generation | FLUX.1-schnell via HuggingFace Router |
| Prompt Enhancement | Gemini 2.5 Flash |
| Icons | lucide-react |

---

## ðŸ“ Project Structure

```
project-root/
â”œâ”€â”€ backend/                          # FastAPI Python backend
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ main.py                   # App factory, CORS, router registration
â”‚   â”‚   â”œâ”€â”€ config.py                 # pydantic-settings env config
â”‚   â”‚   â”œâ”€â”€ api/routes/
â”‚   â”‚   â”‚   â”œâ”€â”€ video.py              # /api/video/* (transcribe, analyze, process, status)
â”‚   â”‚   â”‚   â”œâ”€â”€ youtube_auth.py       # /api/auth/youtube/* (OAuth 2.0)
â”‚   â”‚   â”‚   â””â”€â”€ publish.py            # /api/publish/youtube (upload + AI suggestions)
â”‚   â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”‚   â”œâ”€â”€ transcription_service.py   # Faster-Whisper integration
â”‚   â”‚   â”‚   â”œâ”€â”€ granite_analyzer.py        # IBM Granite 3.0 LLM + JSON validation
â”‚   â”‚   â”‚   â”œâ”€â”€ video_processor.py         # FFmpeg 9:16 smart crop pipeline
â”‚   â”‚   â”‚   â”œâ”€â”€ subtitle_service.py        # .srt karaoke caption generation
â”‚   â”‚   â”‚   â”œâ”€â”€ youtube_service.py         # yt-dlp YouTube download
â”‚   â”‚   â”‚   â””â”€â”€ youtube_publisher.py       # YouTube Data API v3 chunked upload
â”‚   â”‚   â”œâ”€â”€ models/                    # Pydantic models
â”‚   â”‚   â”œâ”€â”€ schemas/                   # JSON Schema for Granite output validation
â”‚   â”‚   â””â”€â”€ utils/                     # FFmpeg + file utilities
â”‚   â”œâ”€â”€ tests/                         # pytest test suite
â”‚   â”œâ”€â”€ requirements.txt
â”‚   â””â”€â”€ .env.example                   # â† Template only, NO real keys
â”‚
â”œâ”€â”€ frontend/                          # Next.js unified frontend
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ page.tsx                   # Tani landing page
â”‚   â”‚   â”œâ”€â”€ studio-upload/             # Video upload form
â”‚   â”‚   â”œâ”€â”€ studio/[jobId]/            # Video clipping studio
â”‚   â”‚   â”œâ”€â”€ auth/youtube/callback/     # OAuth 2.0 callback page
â”‚   â”‚   â”œâ”€â”€ features/
â”‚   â”‚   â”‚   â”œâ”€â”€ video-clipping/        # Feature showcase â†’ studio
â”‚   â”‚   â”‚   â”œâ”€â”€ text-to-image/         # Text-to-image workspace
â”‚   â”‚   â”‚   â””â”€â”€ thumbnail-generator/   # Thumbnail generator workspace
â”‚   â”‚   â””â”€â”€ api/
â”‚   â”‚       â”œâ”€â”€ generate-image/        # FLUX.1 image generation
â”‚   â”‚       â”œâ”€â”€ enhance-prompt/        # Gemini prompt enhancement
â”‚   â”‚       â””â”€â”€ generate-thumbnail/    # Gemini + FLUX thumbnail
â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ home/                      # 9 landing page sections
â”‚   â”‚   â”œâ”€â”€ features/                  # Feature workspaces
â”‚   â”‚   â”œâ”€â”€ studio/                    # Video studio components
â”‚   â”‚   â”œâ”€â”€ upload/                    # Upload + progress components
â”‚   â”‚   â”œâ”€â”€ site-nav.tsx               # Sticky dark navigation
â”‚   â”‚   â””â”€â”€ site-footer.tsx            # Footer
â”‚   â”œâ”€â”€ lib/api.ts                     # Typed fetch wrappers
â”‚   â”œâ”€â”€ lib/types.ts                   # TypeScript interfaces
â”‚   â””â”€â”€ .env.local.example             # â† Template only, NO real keys
â”‚
â”œâ”€â”€ README.md                          # This file
â”œâ”€â”€ .gitignore                         # Blocks all .env files
â””â”€â”€ tasks.md                           # Full implementation spec
```

---

## ðŸš€ Quick Start

### Prerequisites
- Python 3.11+ Â· Node.js 20+ Â· FFmpeg on PATH
- HuggingFace account (free tier) Â· Google Cloud project

### 1. Clone
```bash
git clone https://github.com/Tanisharma122/AI-Builders-Challeneg---IBM-BOB.git
cd AI-Builders-Challeneg---IBM-BOB
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # Fill in your values
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # Fill in your values
npm run dev
```

### 4. Open
```
http://localhost:3000
```

---

## ðŸ”‘ Environment Variables

### `backend/.env` (copy from `.env.example`)
```env
HF_API_KEY=hf_xxxx                    # HuggingFace â€” IBM Granite 3.0 inference
HF_TOKEN=hf_xxxx                      # HuggingFace â€” Pyannote gated model
WHISPER_MODEL_SIZE=base               # tiny | base | small | medium | large-v3
UPLOAD_DIR=/tmp/videoclip/uploads
OUTPUT_DIR=/tmp/videoclip/outputs
FFMPEG_PATH=ffmpeg
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REDIRECT_URI=http://localhost:3000/auth/youtube/callback
CORS_ORIGINS=["http://localhost:3000"]
```

### `frontend/.env.local` (copy from `.env.local.example`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
GEMINI_API_KEY=your_gemini_key
HF_TOKEN=hf_xxxx
```

---

## ðŸ“¡ API Reference

### Video Pipeline
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/video/transcribe` | Upload file or YouTube URL â†’ start job |
| `POST` | `/api/video/analyze` | Trigger IBM Granite viral analysis |
| `POST` | `/api/video/process` | Render 9:16 clips with FFmpeg |
| `GET` | `/api/video/status/{job_id}` | Poll job status + progress % |
| `GET` | `/api/video/analysis/{job_id}` | Fetch Granite analysis JSON |

### YouTube Publishing
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/auth/youtube/login` | Get Google OAuth consent URL |
| `GET` | `/api/auth/youtube/callback` | Exchange code for tokens |
| `POST` | `/api/publish/youtube` | Upload clip â†’ returns live Shorts URL |
| `POST` | `/api/publish/youtube/suggest` | AI title + description + tag suggestions |

---

## ðŸ” Security

- **No API keys are committed** â€” all secrets live in `.env` / `.env.local` (git-ignored)
- `.gitignore` blocks all `*.env*` patterns at both root and frontend level
- Only `.env.example` and `.env.local.example` templates (with placeholder values) are tracked
- YouTube tokens are stored in `sessionStorage` only â€” never sent to backend without explicit publish action

---

## ðŸ—º User Journey

```
http://localhost:3000 (Landing)
        â†“
/features/video-clipping  â†’  "Start Clipping â†’"
        â†“
/studio-upload  (Upload video or paste YouTube URL)
        â†“
/studio/{jobId}  (Live processing: Transcribe â†’ Analyze â†’ Render)
        â†“
Studio: Preview clips Â· Download Â· Publish to YouTube Shorts
        â†“
https://youtube.com/shorts/{video_id}  âœ… LIVE
```

---

## ðŸ“„ License

MIT â€” Built for the **IBM AI Builders Challenge 2025**.

---

<div align="center">

**Made with â¤ï¸ using IBM Bob Â· IBM Granite 3.0 Â· IBM watsonx.ai**

*Tani â€” Empowering Next-Gen Creators with Agentic Content Orchestration*

</div>

