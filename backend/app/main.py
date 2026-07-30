"""
FastAPI application entry point.

Sets up:
- Lifespan events (startup / shutdown)
- CORS middleware
- API router registration
- Health-check endpoint
- Static file serving for processed outputs
"""

from __future__ import annotations

import logging
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes.video import router as video_router
from app.api.routes.youtube_auth import router as youtube_auth_router
from app.api.routes.publish import router as publish_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """
    Startup: verify FFmpeg is available and ensure storage directories exist.
    Shutdown: nothing to clean up (model lives in memory until process exits).
    """
    # Verify FFmpeg is reachable
    if not shutil.which(settings.ffmpeg_path):
        logger.error(
            "FFmpeg not found at '%s'. Video processing will fail. "
            "Install FFmpeg and ensure it is on PATH (or set FFMPEG_PATH).",
            settings.ffmpeg_path,
        )
    else:
        logger.info("FFmpeg found at: %s", shutil.which(settings.ffmpeg_path))

    # Ensure storage directories exist
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Upload dir : %s", settings.upload_dir)
    logger.info("Output dir : %s", settings.output_dir)

    yield  # ← application runs here

    logger.info("Shutting down Video Clipping Engine.")


# ── App factory ───────────────────────────────────────────────────────────────


app = FastAPI(
    title="Video Clipping & Script Generation Engine",
    description=(
        "Accepts video files or YouTube URLs, transcribes them with Faster-Whisper, "
        "analyses viral segments with IBM Granite 3.0, and renders 9:16 clips with FFmpeg."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(video_router)
app.include_router(youtube_auth_router)
app.include_router(publish_router)

# ── Static files (processed clips served directly) ───────────────────────────

app.mount(
    "/outputs",
    StaticFiles(directory=str(settings.output_dir), check_dir=False),
    name="outputs",
)

# ── Health check ──────────────────────────────────────────────────────────────


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Lightweight liveness probe for load balancers and Docker HEALTHCHECK."""
    return {"status": "ok", "version": app.version}
