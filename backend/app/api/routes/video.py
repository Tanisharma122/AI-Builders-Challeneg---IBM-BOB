"""
FastAPI router for video ingestion, transcription, and Granite analysis.

Endpoints
---------
POST /api/video/transcribe  — accept file upload OR YouTube URL, kick off transcription
POST /api/video/analyze     — trigger Granite LLM analysis on a completed transcript
GET  /api/video/status/{job_id} — poll current job state
"""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.models.job import JobStatus, ProcessingJob
from app.services.transcription_service import transcribe_video
from app.services.youtube_service import download_youtube_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video", tags=["video"])

# ── In-memory job store (replaced by DB in production) ────────────────────────
# Imported and used by main.py as well via app.state
_jobs: dict[str, ProcessingJob] = {}


def get_jobs() -> dict[str, ProcessingJob]:
    return _jobs


# ── Background task implementation ────────────────────────────────────────────


def _run_transcription(job_id: str, video_path: Path) -> None:
    """Background task: transcribe *video_path* and update job state."""
    job = _jobs.get(job_id)
    if job is None:
        logger.error("[%s] Job not found in store — aborting.", job_id)
        return

    try:
        job.advance(JobStatus.TRANSCRIBING, progress_pct=10)
        transcript = transcribe_video(video_path, job_id)
        # ANALYZING signals frontend: transcription done, ready for Granite
        job.advance(JobStatus.ANALYZING, progress_pct=30)
        logger.info(
            "[%s] Transcription complete: %d segments.", job_id, len(transcript.segments)
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] Transcription failed.", job_id)
        job.fail(str(exc))


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.post("/transcribe")
async def transcribe_endpoint(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(default=None),
    youtube_url: Optional[str] = Form(default=None),
) -> JSONResponse:
    """
    Accept either a video file upload **or** a YouTube URL (not both, not neither).

    Returns ``{"job_id": "...", "status": "PENDING"}`` immediately; transcription
    runs in the background.
    """

    # ── Input validation ──────────────────────────────────────────────────────
    has_file = file is not None and file.filename not in ("", None)
    has_url = youtube_url not in ("", None)

    if has_file and has_url:
        raise HTTPException(
            status_code=422,
            detail="Provide either a file upload or a YouTube URL — not both.",
        )
    if not has_file and not has_url:
        raise HTTPException(
            status_code=422,
            detail="You must provide either a 'file' upload or a 'youtube_url' field.",
        )

    # ── Create job record ─────────────────────────────────────────────────────
    job_id = str(uuid.uuid4())
    job = ProcessingJob(job_id=job_id)

    if has_file:
        job.source_filename = file.filename  # type: ignore[union-attr]
    else:
        job.youtube_url = youtube_url

    _jobs[job_id] = job

    # ── Resolve local video path ──────────────────────────────────────────────
    job_upload_dir = settings.upload_dir / job_id
    job_upload_dir.mkdir(parents=True, exist_ok=True)
    video_path = job_upload_dir / "source.mp4"

    if has_file:
        # Stream upload to disk to avoid loading into memory
        total_bytes = 0
        max_bytes = settings.max_upload_size_bytes
        try:
            with video_path.open("wb") as dest:
                while chunk := await file.read(1024 * 1024):  # type: ignore[union-attr]
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        dest.close()
                        video_path.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=413,
                            detail=(
                                f"File exceeds maximum upload size of "
                                f"{settings.max_upload_size_mb} MB."
                            ),
                        )
                    dest.write(chunk)
        except HTTPException:
            _jobs.pop(job_id, None)
            raise
        except Exception as exc:
            _jobs.pop(job_id, None)
            raise HTTPException(status_code=500, detail=f"File save error: {exc}") from exc
    else:
        # YouTube download happens inside the background task to keep the
        # response fast; pre-validate the URL format here.
        from app.services.youtube_service import _validate_youtube_url  # noqa: PLC0415

        try:
            _validate_youtube_url(youtube_url)  # type: ignore[arg-type]
        except ValueError as exc:
            _jobs.pop(job_id, None)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        # Override the background task to include YT download step
        def _run_yt_then_transcribe(j_id: str, url: str, out_dir: Path) -> None:
            j = _jobs.get(j_id)
            if j is None:
                return
            try:
                j.advance(JobStatus.TRANSCRIBING, progress_pct=5)
                dl_path = download_youtube_video(url, out_dir)
                transcribe_video(dl_path, j_id)
                # ANALYZING signals frontend: transcription done, ready for Granite
                j.advance(JobStatus.ANALYZING, progress_pct=30)
            except Exception as exc2:  # noqa: BLE001
                logger.exception("[%s] YT download/transcription failed.", j_id)
                j.fail(str(exc2))

        background_tasks.add_task(
            _run_yt_then_transcribe, job_id, youtube_url, job_upload_dir
        )
        return JSONResponse({"job_id": job_id, "status": job.status.value})

    background_tasks.add_task(_run_transcription, job_id, video_path)
    return JSONResponse({"job_id": job_id, "status": job.status.value})


# ── Analyze endpoint (S2-T05) ─────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    job_id: str


def _run_analysis(job_id: str) -> None:
    """Background task: load transcript, run Granite analysis, update job state."""
    from app.services.granite_analyzer import analyze_transcript  # local import avoids circular
    from app.services.transcription_service import load_transcript

    job = _jobs.get(job_id)
    if job is None:
        logger.error("[%s] Job not found for analysis — aborting.", job_id)
        return

    try:
        job.advance(JobStatus.ANALYZING, progress_pct=50)
        transcript = load_transcript(job_id)
        analyze_transcript(transcript, job_id)
        # Use PROCESSING (not COMPLETE) so frontend knows to trigger clip rendering
        job.advance(JobStatus.PROCESSING, progress_pct=60)
        logger.info("[%s] Granite analysis complete — ready for clip processing.", job_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] Granite analysis failed.", job_id)
        job.fail(str(exc))


@router.post("/analyze")
async def analyze_endpoint(
    body: AnalyzeRequest,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Trigger IBM Granite 3.0 viral analysis for a job whose transcript is ready.

    Expects the transcript to have been previously written to
    ``{OUTPUT_DIR}/{job_id}/transcript.json`` by the transcribe endpoint.
    """
    job_id = body.job_id
    job = _jobs.get(job_id)

    if job is None:
        # Job may have been created in a previous server session — create a
        # lightweight placeholder so status polling still works.
        job = ProcessingJob(job_id=job_id)
        _jobs[job_id] = job

    # Verify transcript exists on disk before dispatching
    transcript_on_disk = settings.output_dir / job_id / "transcript.json"
    if not transcript_on_disk.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"No transcript found for job '{job_id}'. "
                "Run /api/video/transcribe first."
            ),
        )

    job.advance(JobStatus.ANALYZING, progress_pct=40)
    background_tasks.add_task(_run_analysis, job_id)
    return JSONResponse({"job_id": job_id, "status": JobStatus.ANALYZING.value})


# ── Process endpoint (S3-T04) ─────────────────────────────────────────────────


class ProcessRequest(BaseModel):
    job_id: str
    clip_ranks: list[int] = []  # empty = process all clips


def _run_processing(job_id: str, clip_ranks: list[int]) -> None:
    """Background task: render clips with FFmpeg, update job state."""
    from app.services.granite_analyzer import load_analysis
    from app.services.transcription_service import load_transcript
    from app.services.video_processor import process_all_clips

    job = _jobs.get(job_id)
    if job is None:
        logger.error("[%s] Job not found for processing — aborting.", job_id)
        return

    try:
        job.advance(JobStatus.PROCESSING, progress_pct=60)

        transcript = load_transcript(job_id)
        analysis = load_analysis(job_id)

        # Locate source video
        source_video = settings.upload_dir / job_id / "source.mp4"
        if not source_video.exists():
            # Try any video file in the upload dir
            candidates = list((settings.upload_dir / job_id).glob("source.*"))
            if not candidates:
                raise FileNotFoundError(
                    f"No source video found for job '{job_id}'."
                )
            source_video = candidates[0]

        ranks = clip_ranks if clip_ranks else None
        output_paths = process_all_clips(
            job_id=job_id,
            analysis=analysis,
            transcript=transcript,
            source_video_path=source_video,
            clip_ranks=ranks,
        )

        clip_path_strs = [str(p) for p in output_paths]
        job.complete(clip_path_strs)
        logger.info(
            "[%s] Processing complete: %d clips rendered.", job_id, len(output_paths)
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] Video processing failed.", job_id)
        job.fail(str(exc))


@router.post("/process")
async def process_endpoint(
    body: ProcessRequest,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Trigger FFmpeg clip rendering for a job that has completed Granite analysis.

    Optionally pass ``clip_ranks`` to render only a subset of clips.
    """
    job_id = body.job_id
    job = _jobs.get(job_id)

    if job is None:
        job = ProcessingJob(job_id=job_id)
        _jobs[job_id] = job

    # Verify both transcript and analysis exist on disk
    analysis_on_disk = settings.output_dir / job_id / "granite_analysis.json"
    if not analysis_on_disk.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"No Granite analysis found for job '{job_id}'. "
                "Run /api/video/analyze first."
            ),
        )

    job.advance(JobStatus.PROCESSING, progress_pct=55)
    background_tasks.add_task(_run_processing, job_id, body.clip_ranks)
    return JSONResponse({"job_id": job_id, "status": JobStatus.PROCESSING.value})


# ── Status endpoint (S3-T05) ──────────────────────────────────────────────────


@router.get("/status/{job_id}")
async def job_status(job_id: str) -> JSONResponse:
    """
    Return the current status of a processing job.

    Response includes:
    - job_id, status, progress_pct, error_msg
    - clip_paths: list of rendered clip file paths (populated on COMPLETE)
    """
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return JSONResponse(job.model_dump(mode="json"))


@router.get("/analysis/{job_id}")
async def get_analysis(job_id: str) -> JSONResponse:
    """Return the Granite analysis JSON for a completed analysis."""
    analysis_path = settings.output_dir / job_id / "granite_analysis.json"
    if not analysis_path.exists():
        raise HTTPException(status_code=404, detail="Analysis not ready yet.")
    import json as _json
    return JSONResponse(_json.loads(analysis_path.read_text(encoding="utf-8")))
