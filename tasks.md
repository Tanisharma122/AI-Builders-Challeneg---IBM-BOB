# Video Clipping & Script Generation Engine — Implementation Plan

> **Module:** Video Clipping & Script Generation Engine
> **Stack:** Python FastAPI · Faster-Whisper/ClipsAI · IBM Granite 3.0 · FFmpeg · Pyannote.audio · Next.js 15 · Tailwind CSS · Shadcn/ui
> **Approach:** Spec-Driven, Sequential 4-Step Implementation

---

## Project Directory Structure

```
project-root/
├── backend/
│   ├── app/
│   │   ├── main.py                         # FastAPI app entry point
│   │   ├── api/+
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── video.py               # /api/video/transcribe & /api/video/clip
│   │   │   │   └── output.py              # /api/output/export
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── transcription_service.py   # Faster-Whisper / ClipsAI integration
│   │   │   ├── youtube_service.py         # yt-dlp YouTube URL ingestion
│   │   │   ├── granite_analyzer.py        # IBM Granite 3.0 LLM service
│   │   │   ├── video_processor.py         # FFmpeg + 9:16 crop pipeline
│   │   │   └── subtitle_service.py        # .srt generation + burn-in
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── transcript.py              # Pydantic: TranscriptWord, TranscriptSegment
│   │   │   ├── granite_output.py          # Pydantic: ViralClip, GraniteAnalysis
│   │   │   └── job.py                     # Pydantic: ProcessingJob, JobStatus
│   │   ├── schemas/
│   │   │   └── granite_output_schema.json # JSON Schema for Granite response validation
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── ffmpeg_utils.py            # FFmpeg command builder helpers
│   │   │   └── file_utils.py              # Temp file management, cleanup
│   │   └── config.py                      # Environment config (HF API key, paths)
│   ├── tests/
│   │   ├── test_transcription.py
│   │   ├── test_granite_analyzer.py
│   │   ├── test_video_processor.py
│   │   └── test_api_routes.py
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx                        # Landing / Upload page
    │   └── studio/
    │       └── [jobId]/
    │           └── page.tsx               # Preview Studio page
    ├── components/
    │   ├── upload/
    │   │   ├── VideoUploader.tsx           # File drop + YouTube URL input
    │   │   └── ProcessingProgress.tsx      # Step-by-step progress bar
    │   ├── studio/
    │   │   ├── VideoPreviewPlayer.tsx      # 9:16 vertical video player
    │   │   ├── GraniteInspectorPanel.tsx   # Script + Virality Score display
    │   │   ├── ClipTimeline.tsx            # Visual clip segment selector
    │   │   └── PlatformOutputTabs.tsx      # YouTube Shorts / IG / LinkedIn / X tabs
    │   └── shared/
    │       ├── StatusBadge.tsx
    │       └── ScoreGauge.tsx              # Virality score visual gauge
    ├── lib/
    │   ├── api.ts                          # Typed fetch wrappers to FastAPI
    │   └── types.ts                        # TypeScript types mirroring Pydantic models
    ├── hooks/
    │   └── useJobPolling.ts               # SSE / polling hook for job status
    ├── next.config.ts
    ├── tailwind.config.ts
    └── package.json
```

---

## Step 1: Video Ingestion & Timestamp Transcription Pipeline

### Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/config.py` | CREATE | Load env vars: HF_API_KEY, UPLOAD_DIR, OUTPUT_DIR, FFMPEG_PATH |
| `backend/app/models/transcript.py` | CREATE | Pydantic models: `TranscriptWord`, `TranscriptSegment`, `FullTranscript` |
| `backend/app/models/job.py` | CREATE | Pydantic models: `ProcessingJob`, `JobStatus` enum |
| `backend/app/services/youtube_service.py` | CREATE | yt-dlp wrapper to download video from YouTube URL to temp file |
| `backend/app/services/transcription_service.py` | CREATE | Faster-Whisper integration with word-level timestamps |
| `backend/app/api/routes/video.py` | CREATE | FastAPI router: `POST /api/video/transcribe` |
| `backend/app/main.py` | CREATE | FastAPI app factory, router registration, CORS, lifespan |
| `backend/requirements.txt` | CREATE | Pin all dependency versions |
| `backend/.env.example` | CREATE | Document required environment variables |

### Checklist — Step 1

- [ ] **S1-T01** Create `backend/app/config.py` — use `pydantic-settings` `BaseSettings` to load `HF_API_KEY`, `UPLOAD_DIR`, `OUTPUT_DIR`, `WHISPER_MODEL_SIZE` (default: `"base"`) from `.env`.
- [ ] **S1-T02** Create `backend/app/models/transcript.py` with three Pydantic models:
  - `TranscriptWord(word: str, start_time: float, end_time: float, probability: float)`
  - `TranscriptSegment(id: int, text: str, start_time: float, end_time: float, words: list[TranscriptWord])`
  - `FullTranscript(job_id: str, language: str, duration: float, segments: list[TranscriptSegment])`
- [ ] **S1-T03** Create `backend/app/models/job.py` — `JobStatus` enum (`PENDING`, `TRANSCRIBING`, `ANALYZING`, `PROCESSING`, `COMPLETE`, `FAILED`), `ProcessingJob` model with `job_id`, `status`, `progress_pct`, `error_msg`.
- [ ] **S1-T04** Create `backend/app/services/youtube_service.py` — `download_youtube_video(url: str, output_dir: Path) -> Path` using `yt-dlp` subprocess call; validate URL format before download; return local file path.
- [ ] **S1-T05** Create `backend/app/services/transcription_service.py`:
  - Load `faster-whisper` `WhisperModel` once at module level (lazy singleton).
  - `transcribe_video(video_path: Path, job_id: str) -> FullTranscript` — extract audio via FFmpeg, run whisper with `word_timestamps=True`, map to `FullTranscript` Pydantic model.
  - Persist transcript JSON to `{OUTPUT_DIR}/{job_id}/transcript.json`.
- [ ] **S1-T06** Create `backend/app/api/routes/video.py`:
  - `POST /api/video/transcribe` — accept `multipart/form-data` with optional `file: UploadFile` OR `youtube_url: str` form field.
  - Validate that exactly one input source is provided; return HTTP 422 otherwise.
  - Save uploaded file to `UPLOAD_DIR/{job_id}/source.mp4`.
  - Dispatch transcription as a `BackgroundTask`; immediately return `{"job_id": ..., "status": "PENDING"}`.
- [ ] **S1-T07** Create `backend/app/main.py` — instantiate `FastAPI`, register CORS middleware (allow Next.js origin), mount `/api/video` router, add `/health` endpoint.
- [ ] **S1-T08** Create `backend/requirements.txt` with pinned versions:
  ```
  fastapi==0.111.0
  uvicorn[standard]==0.30.1
  python-multipart==0.0.9
  pydantic-settings==2.3.4
  faster-whisper==1.0.3
  yt-dlp==2024.5.27
  pyannote.audio==3.3.2
  huggingface_hub==0.23.4
  jsonschema==4.22.0
  ffmpeg-python==0.2.0
  ```
- [ ] **S1-T09** Write `backend/tests/test_transcription.py` — unit test with a 10-second local `.mp4` fixture; assert `FullTranscript` has non-empty `segments`, each segment has `start_time < end_time`.
- [ ] **S1-T10** Create `backend/.env.example` documenting all required variables.

**Edge Cases & Mitigations — Step 1**

| Edge Case | Mitigation |
|-----------|-----------|
| YouTube URL geo-block / private video | Catch `yt-dlp` non-zero exit code; return HTTP 400 with descriptive error |
| Upload exceeds server memory | Set FastAPI `max_upload_size` limit (500 MB); stream file to disk in chunks |
| Whisper OOM on large video | Chunk audio into 10-min segments using FFmpeg `-ss`/`-t` before transcribing; merge results |
| Non-English audio | Auto-detect language via Whisper `detect_language()`; pass `language` param if user specifies |
| Corrupted/unsupported video container | Run `ffprobe` before transcription; return 422 if container is invalid |

---

## Step 2: IBM Granite Viral Segment Analysis & Script Engine

### Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/models/granite_output.py` | CREATE | Pydantic models for Granite structured output |
| `backend/app/schemas/granite_output_schema.json` | CREATE | JSON Schema for strict validation of Granite LLM response |
| `backend/app/services/granite_analyzer.py` | CREATE | IBM Granite 3.0 HuggingFace API client + prompt builder |
| `backend/app/api/routes/video.py` | MODIFY | Add `POST /api/video/analyze` endpoint |

### Checklist — Step 2

- [ ] **S2-T01** Create `backend/app/models/granite_output.py`:
  - `ViralClip(rank: int, start_time: float, end_time: float, hook_text: str, script_commentary: str, virality_score: int, virality_reasoning: str)`
  - `GraniteAnalysis(job_id: str, clips: list[ViralClip], model_used: str, tokens_used: int)`
  - Add `@validator` on `virality_score` to assert `0 <= value <= 100`.
- [ ] **S2-T02** Create `backend/app/schemas/granite_output_schema.json` — strict JSON Schema with `"additionalProperties": false` for the Granite response envelope:
  ```json
  {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["clips"],
    "properties": {
      "clips": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["rank","start_time","end_time","hook_text","script_commentary","virality_score","virality_reasoning"],
          "properties": {
            "rank": {"type": "integer"},
            "start_time": {"type": "number"},
            "end_time": {"type": "number"},
            "hook_text": {"type": "string", "maxLength": 100},
            "script_commentary": {"type": "string"},
            "virality_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "virality_reasoning": {"type": "string"}
          },
          "additionalProperties": false
        }
      }
    }
  }
  ```
- [ ] **S2-T03** Create `backend/app/services/granite_analyzer.py`:
  - `_build_prompt(transcript: FullTranscript) -> str` — construct system + user prompt instructing Granite to return **only** a raw JSON object (no markdown fences), identifying top 5 viral clips.
  - Prompt template must include: role instruction, transcript JSON (compacted), explicit output format example, instruction to not wrap in markdown.
  - `_call_granite_api(prompt: str) -> str` — call `ibm-granite/granite-3.0-8b-instruct` via `huggingface_hub.InferenceClient`; set `max_new_tokens=2048`, `temperature=0.2`.
  - `_validate_and_parse(raw: str) -> dict` — strip any accidental markdown fences with regex, run `jsonschema.validate()` against `granite_output_schema.json`; raise `GraniteOutputValidationError` on failure.
  - `analyze_transcript(transcript: FullTranscript, job_id: str) -> GraniteAnalysis` — orchestrates the above three private functions; persist result to `{OUTPUT_DIR}/{job_id}/granite_analysis.json`.
- [ ] **S2-T04** Implement retry logic in `granite_analyzer.py`:
  - Wrap `_call_granite_api` with `tenacity` `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))`.
  - On `HfHubHTTPError` with status 429 (rate limit), log warning and retry.
- [ ] **S2-T05** Modify `backend/app/api/routes/video.py` — add `POST /api/video/analyze`:
  - Accept `{"job_id": "..."}` JSON body.
  - Load transcript JSON from disk; deserialize to `FullTranscript`.
  - Call `analyze_transcript()` as `BackgroundTask`.
  - Return `{"job_id": ..., "status": "ANALYZING"}`.
- [ ] **S2-T06** Write `backend/tests/test_granite_analyzer.py`:
  - Unit test `_validate_and_parse` with a valid JSON fixture — assert returns `GraniteAnalysis` with 5 clips.
  - Unit test `_validate_and_parse` with invalid JSON — assert raises `GraniteOutputValidationError`.
  - Mock `_call_granite_api` to avoid real API calls in CI.

**Edge Cases & Mitigations — Step 2**

| Edge Case | Mitigation |
|-----------|-----------|
| HuggingFace free tier rate limit (429) | `tenacity` exponential backoff retry (max 3 attempts); surface error to UI after exhaustion |
| Granite returns malformed / partial JSON | Regex strip markdown fences + `jsonschema` validation; on failure retry with stricter prompt instructing JSON-only |
| Transcript too long for context window (8192 tokens) | Truncate to first 6000 tokens of transcript text; log a warning; use sentence-level granularity instead of word-level |
| Granite hallucinates `start_time` outside video duration | Post-validation: clamp `start_time`/`end_time` against actual `transcript.duration`; discard clips with `end_time - start_time < 5s` |
| HuggingFace API key missing / invalid | Check on startup in `config.py`; raise `ValueError` with clear message before accepting requests |
| Ollama local fallback | Add `USE_OLLAMA: bool` config flag; if `True`, route to `http://localhost:11434/api/generate` instead of HF API |

---

## Step 3: 9:16 Smart Reframing & FFmpeg Subtitle Rendering

### Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/utils/ffmpeg_utils.py` | CREATE | FFmpeg command builder: trim, crop, subtitle burn-in |
| `backend/app/services/subtitle_service.py` | CREATE | Generate `.srt` files from transcript words |
| `backend/app/services/video_processor.py` | CREATE | Pyannote speaker tracking + 9:16 crop orchestration |
| `backend/app/api/routes/video.py` | MODIFY | Add `POST /api/video/process` endpoint |

### Checklist — Step 3

- [ ] **S3-T01** Create `backend/app/utils/ffmpeg_utils.py`:
  - `probe_video(path: Path) -> dict` — run `ffprobe -v quiet -print_format json -show_streams` and return parsed dict.
  - `extract_audio(video_path: Path, output_path: Path) -> None` — FFmpeg command: `-vn -acodec pcm_s16le -ar 16000 -ac 1`.
  - `build_crop_filter(src_w: int, src_h: int, crop_x: int) -> str` — compute 9:16 crop: target width = `src_h * 9 // 16`; return `f"crop={target_w}:{src_h}:{crop_x}:0,scale=1080:1920"`.
  - `build_trim_and_crop_command(src: Path, out: Path, start: float, end: float, crop_filter: str, srt_path: Path) -> list[str]` — assemble full FFmpeg argument list with `-ss`, `-to`, `-vf` combining crop + `subtitles=` filter, `-c:v libx264 -preset fast -crf 23 -c:a aac`.
  - `run_ffmpeg(cmd: list[str], timeout: int = 120) -> None` — subprocess call with `timeout`; raise `FFmpegError` on non-zero exit or timeout.
- [ ] **S3-T02** Create `backend/app/services/subtitle_service.py`:
  - `generate_srt(segment: TranscriptSegment, output_path: Path, max_chars_per_line: int = 40) -> Path` — iterate over `segment.words`, group into subtitle blocks of ≤ `max_chars_per_line` chars, write `.srt` format with sequence number, `HH:MM:SS,mmm --> HH:MM:SS,mmm`, and text.
  - Style captions with all-caps, word-level timing for "karaoke" effect.
- [ ] **S3-T03** Create `backend/app/services/video_processor.py`:
  - `initialize_diarization() -> Pipeline` — load `pyannote/speaker-diarization-3.1` pipeline once; requires HuggingFace token.
  - `get_dominant_speaker_bbox(diarization, start: float, end: float, video_path: Path) -> int` — sample frames in the clip window using `pyannote.audio` speaker timestamps; extract speaker bounding box from representative frame using `ffmpeg` frame extraction; return `crop_x` offset. Fall back to center crop if diarization confidence < 0.6.
  - `process_clip(job_id: str, clip: ViralClip, transcript: FullTranscript) -> Path`:
    1. Call `probe_video()` to get source dimensions.
    2. Find transcript segments overlapping `clip.start_time` to `clip.end_time`.
    3. Call `generate_srt()` for those segments.
    4. Call `get_dominant_speaker_bbox()` to determine crop X.
    5. Build crop filter with `build_crop_filter()`.
    6. Build and run full FFmpeg command.
    7. Return output path `{OUTPUT_DIR}/{job_id}/clip_{clip.rank}.mp4`.
  - `process_all_clips(job_id: str, analysis: GraniteAnalysis, transcript: FullTranscript) -> list[Path]` — iterate over all clips, call `process_clip()` for each, return list of output paths.
- [ ] **S3-T04** Modify `backend/app/api/routes/video.py` — add `POST /api/video/process`:
  - Accept `{"job_id": "...", "clip_ranks": [1, 2, 3]}` — allow processing a subset of clips.
  - Load `GraniteAnalysis` and `FullTranscript` from disk.
  - Run `process_all_clips()` as `BackgroundTask`.
  - Return `{"job_id": ..., "status": "PROCESSING"}`.
- [ ] **S3-T05** Add `GET /api/video/status/{job_id}` endpoint — read `ProcessingJob` state from an in-memory dict (or Redis if available); return `JobStatus` + `progress_pct` + list of completed clip paths.
- [ ] **S3-T06** Write `backend/tests/test_video_processor.py`:
  - Test `build_crop_filter(1920, 1080, 420)` returns correct FFmpeg filter string.
  - Test `generate_srt()` with 5-word `TranscriptSegment` fixture produces valid `.srt` format.
  - Integration test `run_ffmpeg()` with a real 5-second clip (CI-safe, small file).

**Edge Cases & Mitigations — Step 3**

| Edge Case | Mitigation |
|-----------|-----------|
| FFmpeg binary not found on PATH | Check `shutil.which("ffmpeg")` at startup; raise `RuntimeError` with install instructions |
| FFmpeg timeout on long clip | Default timeout 120s per clip; configurable via `FFMPEG_TIMEOUT` env var; kill subprocess on timeout |
| Pyannote diarization fails / no speaker detected | Fall back to center crop (`crop_x = (src_w - target_w) // 2`); log warning |
| Source video already vertical (9:16 or portrait) | `probe_video()` check: if `width < height`, skip crop filter; just trim + add subtitles |
| Subtitle `.srt` has empty text blocks | Guard: skip subtitle blocks with empty `word` text; FFmpeg `subtitles` filter is tolerant but defensive is better |
| Concurrent clip processing OOM | Limit concurrency with `asyncio.Semaphore(2)` in `process_all_clips()`; process clips sequentially on low-memory hosts |
| Disk space exhaustion | Check available disk before processing with `shutil.disk_usage()`; require at least 2× source video size free |

---

## Step 4: Next.js Preview Studio UI Wiring

### Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/lib/types.ts` | CREATE | TypeScript interfaces mirroring Pydantic models |
| `frontend/lib/api.ts` | CREATE | Typed `fetch` wrappers for all FastAPI endpoints |
| `frontend/hooks/useJobPolling.ts` | CREATE | Polling hook for job status updates |
| `frontend/components/upload/VideoUploader.tsx` | CREATE | File drag-drop + YouTube URL form |
| `frontend/components/upload/ProcessingProgress.tsx` | CREATE | Step-based animated progress indicator |
| `frontend/components/studio/VideoPreviewPlayer.tsx` | CREATE | 9:16 vertical `<video>` player with controls |
| `frontend/components/studio/GraniteInspectorPanel.tsx` | CREATE | Script, hook text, and virality score display |
| `frontend/components/studio/ClipTimeline.tsx` | CREATE | Horizontal clip segment cards |
| `frontend/components/studio/PlatformOutputTabs.tsx` | CREATE | Tab panel for platform-specific exports |
| `frontend/components/shared/ScoreGauge.tsx` | CREATE | SVG arc gauge for virality score |
| `frontend/app/page.tsx` | CREATE | Landing page with uploader |
| `frontend/app/studio/[jobId]/page.tsx` | CREATE | Studio page composing all studio components |
| `frontend/next.config.ts` | CREATE | Proxy `/api` to FastAPI backend |

### Checklist — Step 4

- [ ] **S4-T01** Create `frontend/lib/types.ts` — define interfaces `TranscriptWord`, `TranscriptSegment`, `FullTranscript`, `ViralClip`, `GraniteAnalysis`, `ProcessingJob` matching backend Pydantic models exactly.
- [ ] **S4-T02** Create `frontend/lib/api.ts`:
  - `uploadVideo(file: File | null, youtubeUrl: string | null): Promise<ProcessingJob>` — `POST /api/video/transcribe` multipart.
  - `analyzeVideo(jobId: string): Promise<ProcessingJob>` — `POST /api/video/analyze`.
  - `processClips(jobId: string, clipRanks: number[]): Promise<ProcessingJob>` — `POST /api/video/process`.
  - `getJobStatus(jobId: string): Promise<ProcessingJob>` — `GET /api/video/status/{jobId}`.
  - All functions throw typed `ApiError` with `status` and `message` on non-2xx.
- [ ] **S4-T03** Create `frontend/hooks/useJobPolling.ts` — custom hook accepting `jobId: string | null`; polls `getJobStatus()` every 2s while `status !== "COMPLETE" && status !== "FAILED"`; returns `{ job, isLoading, error }`; clears interval on unmount.
- [ ] **S4-T04** Create `frontend/components/upload/VideoUploader.tsx`:
  - Shadcn `Card` container with two tabs: "Upload File" and "YouTube URL".
  - File tab: HTML5 drag-and-drop zone accepting `video/*`; show file name + size on drop.
  - URL tab: `Input` + `Button` for YouTube URL submission.
  - On submit: call `uploadVideo()`, navigate to `/studio/{jobId}` on success.
- [ ] **S4-T05** Create `frontend/components/upload/ProcessingProgress.tsx`:
  - Accept `job: ProcessingJob` prop.
  - Render 4-step pipeline: `Transcribing → Analyzing → Processing → Complete`.
  - Map `JobStatus` enum to active step; animate active step with Tailwind `animate-pulse`.
  - Display `progress_pct` as a Shadcn `Progress` bar.
- [ ] **S4-T06** Create `frontend/components/studio/VideoPreviewPlayer.tsx`:
  - `<video>` element constrained to `aspect-[9/16]` Tailwind class, max-height `80vh`.
  - Accept `src: string` and `clipRank: number` props.
  - Custom play/pause/scrub controls styled with Tailwind.
  - Show clip rank badge overlay.
- [ ] **S4-T07** Create `frontend/components/studio/GraniteInspectorPanel.tsx`:
  - Accept `clip: ViralClip` prop.
  - Section 1 — **Hook Text**: Large bold text display with copy-to-clipboard button.
  - Section 2 — **Script Commentary**: Scrollable text area (read-only) with Shadcn `ScrollArea`.
  - Section 3 — **Virality Score**: `ScoreGauge` component + reasoning text in muted style.
  - Section 4 — **Timestamps**: `start_time` → `end_time` formatted as `MM:SS`.
- [ ] **S4-T08** Create `frontend/components/shared/ScoreGauge.tsx` — SVG arc gauge (180° semi-circle); score 0–100 maps to arc fill; color ramp: `<40` red, `40–70` amber, `>70` green; display numeric score in center.
- [ ] **S4-T09** Create `frontend/components/studio/ClipTimeline.tsx`:
  - Horizontal scroll row of `ViralClip` cards.
  - Each card shows rank, `hook_text` truncated, `virality_score` badge, duration.
  - Active clip highlighted with `ring-2 ring-blue-500`.
  - On card click: update selected clip state, seek `VideoPreviewPlayer` to clip.
- [ ] **S4-T10** Create `frontend/components/studio/PlatformOutputTabs.tsx`:
  - Shadcn `Tabs` with 4 tabs: **YouTube Shorts**, **Instagram Reels**, **LinkedIn**, **X (Twitter)**.
  - Each tab shows: recommended aspect ratio, max duration, character limit for hook text, download button triggering `/api/output/export?job_id=...&clip=...&platform=...`.
  - Show platform-specific warnings (e.g., LinkedIn does not support vertical-only).
- [ ] **S4-T11** Create `frontend/app/studio/[jobId]/page.tsx`:
  - Server component fetching initial job state.
  - If job not complete: render `ProcessingProgress` with `useJobPolling`.
  - If job complete: render 2-column layout — left `VideoPreviewPlayer` + `ClipTimeline`, right `GraniteInspectorPanel` + `PlatformOutputTabs`.
- [ ] **S4-T12** Create `frontend/next.config.ts` — add `rewrites` to proxy `/api/:path*` to `http://localhost:8000/api/:path*` for local development.
- [ ] **S4-T13** Update `frontend/tailwind.config.ts` — add `aspect-ratio` plugin, configure content paths including `components/**/*.tsx`.

**Edge Cases & Mitigations — Step 4**

| Edge Case | Mitigation |
|-----------|-----------|
| User navigates away before job completes | `useJobPolling` cleans up interval on `useEffect` unmount; job continues server-side |
| Backend returns `FAILED` status | Display Shadcn `Alert` with `error_msg` from job; show "Retry" button re-triggering analysis |
| Video preview CORS on served files | Configure FastAPI `StaticFiles` with correct `Access-Control-Allow-Origin` header |
| Slow network — video preview stalls | Use `<video preload="metadata">` only; load full video on play event |
| Multiple rapid platform tab switches | Debounce download requests with 500ms `useCallback` debounce to prevent duplicate exports |
| Job ID not found (stale URL) | 404 redirect from `studio/[jobId]/page.tsx` to home page with toast notification |

---

## Master Task Checklist (Agent Mode Execution Order)

```
### PHASE 1 — Backend Foundation
- [ ] S1-T01  config.py (pydantic-settings)
- [ ] S1-T02  models/transcript.py
- [ ] S1-T03  models/job.py
- [ ] S1-T04  services/youtube_service.py
- [ ] S1-T05  services/transcription_service.py
- [ ] S1-T06  api/routes/video.py (transcribe endpoint)
- [ ] S1-T07  main.py
- [ ] S1-T08  requirements.txt
- [ ] S1-T09  tests/test_transcription.py
- [ ] S1-T10  .env.example

### PHASE 2 — LLM Analysis Layer
- [ ] S2-T01  models/granite_output.py
- [ ] S2-T02  schemas/granite_output_schema.json
- [ ] S2-T03  services/granite_analyzer.py
- [ ] S2-T04  Retry logic (tenacity) in granite_analyzer.py
- [ ] S2-T05  api/routes/video.py (analyze endpoint)
- [ ] S2-T06  tests/test_granite_analyzer.py

### PHASE 3 — Video Processing Pipeline
- [ ] S3-T01  utils/ffmpeg_utils.py
- [ ] S3-T02  services/subtitle_service.py
- [ ] S3-T03  services/video_processor.py
- [ ] S3-T04  api/routes/video.py (process endpoint)
- [ ] S3-T05  api/routes/video.py (status endpoint)
- [ ] S3-T06  tests/test_video_processor.py

### PHASE 4 — Frontend Studio
- [ ] S4-T01  lib/types.ts
- [ ] S4-T02  lib/api.ts
- [ ] S4-T03  hooks/useJobPolling.ts
- [ ] S4-T04  components/upload/VideoUploader.tsx
- [ ] S4-T05  components/upload/ProcessingProgress.tsx
- [ ] S4-T06  components/studio/VideoPreviewPlayer.tsx
- [ ] S4-T07  components/studio/GraniteInspectorPanel.tsx
- [ ] S4-T08  components/shared/ScoreGauge.tsx
- [ ] S4-T09  components/studio/ClipTimeline.tsx
- [ ] S4-T10  components/studio/PlatformOutputTabs.tsx
- [ ] S4-T11  app/studio/[jobId]/page.tsx
- [ ] S4-T12  next.config.ts
- [ ] S4-T13  tailwind.config.ts
```

---

## Global Edge Cases & Cross-Cutting Concerns

| Concern | File(s) | Mitigation |
|---------|---------|-----------|
| Job state persistence across server restarts | `models/job.py` + `main.py` | Replace in-memory dict with SQLite via `aiosqlite`; use `job_id` as PK |
| Temp file cleanup | `utils/file_utils.py` | `cleanup_job_files(job_id)` deletes `UPLOAD_DIR/{job_id}` after export download; add TTL-based cron |
| Concurrent upload storms | `api/routes/video.py` | Limit active jobs with a `asyncio.Semaphore`; return HTTP 503 when at capacity |
| HuggingFace token for Pyannote (gated model) | `config.py` | Separate `HF_TOKEN` env var; document acceptance of pyannote usage terms in README |
| FFmpeg not available in Docker | `Dockerfile` | Base image `linuxserver/ffmpeg` or install via `apt-get install ffmpeg` in build stage |
| HTTPS in production (mixed-content) | `next.config.ts` | Use env-based `NEXT_PUBLIC_API_URL`; reverse-proxy FastAPI behind nginx with TLS |

---

## Environment Variables Reference

```env
# backend/.env
HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxx       # HuggingFace Inference API key
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx         # HuggingFace token (for Pyannote gated model)
WHISPER_MODEL_SIZE=base                  # Options: tiny, base, small, medium, large-v3
UPLOAD_DIR=/tmp/videoclip/uploads
OUTPUT_DIR=/tmp/videoclip/outputs
FFMPEG_PATH=ffmpeg                       # or absolute path if not on PATH
FFMPEG_TIMEOUT=120                       # seconds per clip
USE_OLLAMA=false                         # set true to use local Ollama instead of HF API
OLLAMA_BASE_URL=http://localhost:11434
MAX_CONCURRENT_JOBS=2

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

*Generated by IBM Bob · Spec-Driven Development Plan · Video Clipping & Script Generation Engine*
