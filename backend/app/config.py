"""
Application configuration loaded from environment variables via pydantic-settings.
Copy backend/.env.example to backend/.env and fill in values before running.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import os

# Resolve .env relative to this file (backend/app/config.py → backend/.env)
# This works regardless of which directory uvicorn / pytest is invoked from.
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8-sig",   # utf-8-sig strips BOM automatically
        case_sensitive=False,
        extra="ignore",
    )

    # ── HuggingFace ───────────────────────────────────────────────────────────
    hf_api_key: str = ""
    """HuggingFace Inference API key — used for IBM Granite 3.0 text generation."""

    hf_token: str = ""
    """HuggingFace token for gated models (pyannote/speaker-diarization-3.1)."""

    # ── Whisper ───────────────────────────────────────────────────────────────
    whisper_model_size: str = "base"
    """Faster-Whisper model size. Options: tiny, base, small, medium, large-v3."""

    # ── File system ───────────────────────────────────────────────────────────
    upload_dir: Path = Path("/tmp/videoclip/uploads")
    """Directory where uploaded / downloaded source videos are stored."""

    output_dir: Path = Path("/tmp/videoclip/outputs")
    """Directory where transcripts, analysis JSON, and processed clips are saved."""

    # ── FFmpeg ────────────────────────────────────────────────────────────────
    ffmpeg_path: str = "ffmpeg"
    """Path to the FFmpeg binary. Defaults to 'ffmpeg' (must be on PATH)."""

    ffmpeg_timeout: int = 120
    """Per-clip FFmpeg processing timeout in seconds."""

    # ── LLM backend ───────────────────────────────────────────────────────────
    use_ollama: bool = False
    """If True, route LLM calls to local Ollama instead of HuggingFace API."""

    ollama_base_url: str = "http://localhost:11434"
    """Base URL for local Ollama server."""

    # ── Concurrency ───────────────────────────────────────────────────────────
    max_concurrent_jobs: int = 2
    """Maximum number of jobs processed concurrently."""

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]
    """Allowed CORS origins (Next.js dev server)."""

    # ── Upload limits ─────────────────────────────────────────────────────────
    max_upload_size_mb: int = 500
    """Maximum allowed upload size in megabytes."""

    # ── YouTube OAuth ─────────────────────────────────────────────────────────
    youtube_client_id: str = ""
    """Google OAuth 2.0 client ID for YouTube Data API v3."""

    youtube_client_secret: str = ""
    """Google OAuth 2.0 client secret."""

    youtube_redirect_uri: str = "http://localhost:3000/auth/youtube/callback"
    """OAuth redirect URI — must match the URI registered in Google Cloud Console."""

    @field_validator("upload_dir", "output_dir", mode="after")
    @classmethod
    def _ensure_dir_exists(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("hf_api_key", mode="after")
    @classmethod
    def _warn_missing_hf_key(cls, v: str) -> str:
        """
        Warn once at startup if HF_API_KEY is absent and no local Ollama
        fallback is configured.

        The warning message starts with ``HF_API_KEY is not set`` so it can
        be suppressed cleanly in pytest via ``filterwarnings``.
        """
        if not v:
            import warnings
            warnings.warn(
                "HF_API_KEY is not set. "
                "HuggingFace Granite API calls will fail. "
                "Set USE_OLLAMA=true to use a local model instead.",
                UserWarning,
                stacklevel=2,
            )
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


# Module-level singleton — import this everywhere
settings = Settings()
