"""
YouTube Shorts publishing endpoint.

Routes
------
POST /api/publish/youtube          — upload a processed clip to YouTube Shorts
GET  /api/publish/youtube/suggest  — generate title/description/tag suggestions
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/publish", tags=["publish"])


# ── Request / Response models ─────────────────────────────────────────────────


class YouTubePublishRequest(BaseModel):
    """Body for POST /api/publish/youtube."""

    job_id: str = Field(..., description="Job ID whose rendered clip to upload.")
    clip_rank: int = Field(1, ge=1, description="Which clip rank to upload (default 1).")
    title: str = Field(..., min_length=1, max_length=100, description="Video title.")
    description: str = Field("", max_length=5000, description="Video description.")
    tags: list[str] = Field(default_factory=list, description="List of tags.")
    token_data: dict = Field(..., description="OAuth token_data from /api/auth/youtube/callback.")
    category_id: str = Field("22", description="YouTube category ID (22 = People & Blogs).")


class SuggestRequest(BaseModel):
    """Body for POST /api/publish/youtube/suggest."""

    hook_text: str = Field(..., description="Clip hook text from Granite analysis.")
    script_commentary: str = Field("", description="Clip script commentary.")
    virality_score: int = Field(50, ge=0, le=100, description="Virality score 0–100.")
    count: int = Field(5, ge=1, le=10, description="Number of suggestions to return.")


# ── Publish endpoint ──────────────────────────────────────────────────────────


@router.post("/youtube")
async def publish_to_youtube(body: YouTubePublishRequest) -> JSONResponse:
    """
    Upload a processed clip to YouTube as a Short.

    - Locates the rendered clip at ``{OUTPUT_DIR}/{job_id}/clip_{clip_rank}.mp4``.
    - Appends ``#Shorts`` to the title automatically.
    - Uses chunked resumable upload to avoid memory spikes.
    - Returns the live ``https://youtube.com/shorts/{id}`` URL on success.

    Error handling:
    - 404 if clip file is not found.
    - 400 if token is expired and cannot be refreshed.
    - 503 if google libraries are not installed.
    - 502 for YouTube API errors (quota, network, etc.).
    """
    clip_path = settings.output_dir / body.job_id / f"clip_{body.clip_rank}.mp4"

    if not clip_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Clip file not found: {clip_path}. "
                "Ensure the job has completed processing before publishing."
            ),
        )

    try:
        from app.services.youtube_publisher import upload_to_youtube
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail=(
                "YouTube publisher dependencies are not installed. "
                "Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
            ),
        )

    try:
        shorts_url = upload_to_youtube(
            video_path=clip_path,
            title=body.title,
            description=body.description,
            tags=body.tags,
            token_data=body.token_data,
            category_id=body.category_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        # Expired / invalid token
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        err_msg = str(exc)
        if "quota" in err_msg.lower():
            raise HTTPException(status_code=429, detail=err_msg) from exc
        raise HTTPException(status_code=502, detail=err_msg) from exc
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        logger.exception("[%s] Unexpected error during YouTube upload.", body.job_id)
        raise HTTPException(status_code=500, detail=f"Upload error: {exc}\n\nTraceback:\n{tb}") from exc

    logger.info("[%s] Clip %d published: %s", body.job_id, body.clip_rank, shorts_url)
    return JSONResponse(
        {
            "shorts_url": shorts_url,
            "job_id": body.job_id,
            "clip_rank": body.clip_rank,
        }
    )


# ── Suggest endpoint ──────────────────────────────────────────────────────────


@router.post("/youtube/suggest")
async def suggest_metadata(body: SuggestRequest) -> JSONResponse:
    """
    Generate AI-powered title, description, and viral tag suggestions.

    Analyzes the clip's hook text and script commentary from Granite to
    produce platform-optimized metadata — no external API call required.
    """
    from app.services.youtube_publisher import (
        generate_description_suggestions,
        generate_title_suggestions,
        generate_viral_tags,
    )

    tags = generate_viral_tags(
        hook_text=body.hook_text,
        script_commentary=body.script_commentary,
        virality_score=body.virality_score,
    )

    titles = generate_title_suggestions(
        hook_text=body.hook_text,
        script_commentary=body.script_commentary,
        virality_score=body.virality_score,
        count=body.count,
    )

    descriptions = generate_description_suggestions(
        hook_text=body.hook_text,
        script_commentary=body.script_commentary,
        virality_score=body.virality_score,
        tags=tags,
        count=3,
    )

    return JSONResponse(
        {
            "title_suggestions": titles,
            "description_suggestions": descriptions,
            "viral_tags": tags,
        }
    )
