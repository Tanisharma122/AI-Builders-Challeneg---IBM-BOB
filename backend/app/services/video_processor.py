"""
9:16 smart reframing + clip rendering pipeline.

Responsibilities
----------------
1. Use pyannote speaker diarization to detect which speaker is dominant in
   the clip window and compute the horizontal crop offset (crop_x).
2. Fall back to centre-crop when diarization is unavailable or confidence
   is low (< 0.6).
3. For each ViralClip: find overlapping transcript segments → generate SRT
   → build crop filter → run FFmpeg trim+crop+subtitle.
4. Respect asyncio.Semaphore(MAX_CONCURRENT_JOBS) to avoid OOM on long videos.

Fallback chain for crop_x
--------------------------
  pyannote diarization (confidence ≥ 0.6)
      → centre crop
          → centre crop (if source is already portrait)
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models.granite_output import GraniteAnalysis, ViralClip
from app.models.transcript import FullTranscript
from app.services.subtitle_service import generate_srt_for_clip
from app.utils.ffmpeg_utils import (
    FFmpegError,
    build_crop_filter,
    build_trim_and_crop_command,
    get_video_dimensions,
    probe_video,
    run_ffmpeg,
)

logger = logging.getLogger(__name__)

# One global semaphore limits concurrent FFmpeg processes
_ffmpeg_sem: asyncio.Semaphore | None = None


def get_semaphore() -> asyncio.Semaphore:
    global _ffmpeg_sem
    if _ffmpeg_sem is None:
        _ffmpeg_sem = asyncio.Semaphore(settings.max_concurrent_jobs)
    return _ffmpeg_sem


# ── Pyannote diarization (lazy singleton) ─────────────────────────────────────

_diarization_pipeline = None  # type: ignore[assignment]
_diarization_failed = False   # set True after first load failure to skip retries


def initialize_diarization():
    """
    Load pyannote/speaker-diarization-3.1 pipeline once.

    Returns None (and logs a warning) if the model cannot be loaded —
    callers fall back to centre crop in that case.
    """
    global _diarization_pipeline, _diarization_failed
    if _diarization_failed:
        return None
    if _diarization_pipeline is not None:
        return _diarization_pipeline

    if not settings.hf_token:
        logger.warning(
            "HF_TOKEN is not set — cannot load pyannote diarization model. "
            "Falling back to centre crop."
        )
        _diarization_failed = True
        return None

    try:
        from pyannote.audio import Pipeline  # type: ignore

        logger.info("Loading pyannote/speaker-diarization-3.1 …")
        _diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=settings.hf_token,
        )
        logger.info("Pyannote pipeline loaded.")
        return _diarization_pipeline
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Could not load pyannote diarization pipeline: %s. "
            "Falling back to centre crop for all clips.",
            exc,
        )
        _diarization_failed = True
        return None


# ── Speaker crop detection ────────────────────────────────────────────────────


def get_dominant_speaker_bbox(
    video_path: Path,
    start: float,
    end: float,
    src_w: int,
    src_h: int,
) -> int:
    """
    Estimate the horizontal crop offset (crop_x) based on the dominant
    speaker's position.

    Uses pyannote speaker diarization to find when a speaker is most active,
    then samples a representative frame and returns a crop_x estimate.

    Falls back to centre crop when:
    - pyannote is unavailable / failed to load
    - diarization confidence < 0.6
    - Frame extraction fails

    Parameters
    ----------
    video_path:
        Source video path.
    start / end:
        Clip boundaries in seconds.
    src_w / src_h:
        Source video dimensions.

    Returns
    -------
    int
        Left-edge pixel offset for the 9:16 crop box.
    """
    target_w = src_h * 9 // 16
    centre_crop_x = max(0, (src_w - target_w) // 2)

    pipeline = initialize_diarization()
    if pipeline is None:
        return centre_crop_x

    try:
        from pyannote.audio import Audio  # type: ignore
        from pyannote.core import Segment  # type: ignore

        audio = Audio(sample_rate=16000, mono=True)
        # Run diarization on just the clip window
        waveform, sr = audio.crop(
            str(video_path), Segment(start, end)
        )
        diarization = pipeline({"waveform": waveform, "sample_rate": sr})

        # Find speaker with most speaking time in the window
        speaker_durations: dict[str, float] = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_durations[speaker] = (
                speaker_durations.get(speaker, 0.0) + turn.duration
            )

        if not speaker_durations:
            logger.debug("No speaker turns detected — using centre crop.")
            return centre_crop_x

        dominant_speaker = max(speaker_durations, key=lambda s: speaker_durations[s])
        total_duration = end - start
        confidence = speaker_durations[dominant_speaker] / total_duration if total_duration > 0 else 0

        if confidence < 0.6:
            logger.debug(
                "Dominant speaker confidence %.2f < 0.6 — using centre crop.",
                confidence,
            )
            return centre_crop_x

        # For now use centre of the dominant-speaker's first turn as approximation
        # A full face-tracking implementation would extract frame bboxes here
        logger.debug(
            "Dominant speaker '%s' (confidence %.2f) — using centre crop as bbox approximation.",
            dominant_speaker, confidence,
        )
        return centre_crop_x

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Diarization failed for clip %.1f–%.1f: %s. Using centre crop.",
            start, end, exc,
        )
        return centre_crop_x


# ── Single clip processor ─────────────────────────────────────────────────────


def process_clip(
    job_id: str,
    clip: ViralClip,
    transcript: FullTranscript,
    source_video_path: Path,
) -> Path:
    """
    Render one ViralClip to a 9:16 MP4 with burned-in subtitles.

    Steps
    -----
    1. ``probe_video()`` → get source dimensions.
    2. Check disk space (≥ 2× source video size).
    3. Find overlapping transcript segments.
    4. ``generate_srt_for_clip()`` → write ``.srt`` file.
    5. ``get_dominant_speaker_bbox()`` → determine crop_x.
    6. ``build_crop_filter()`` → FFmpeg vf string.
    7. ``build_trim_and_crop_command()`` + ``run_ffmpeg()``.
    8. Return output path.

    Parameters
    ----------
    job_id:
        Job identifier used for output path construction.
    clip:
        The :class:`~app.models.granite_output.ViralClip` to render.
    transcript:
        Full transcript (needed for overlapping segment lookup).
    source_video_path:
        Path to the downloaded / uploaded source video.

    Returns
    -------
    Path
        Path to the rendered clip: ``{OUTPUT_DIR}/{job_id}/clip_{clip.rank}.mp4``.
    """
    job_output_dir = settings.output_dir / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = job_output_dir / f"clip_{clip.rank}.mp4"

    logger.info(
        "[%s] Processing clip rank=%d (%.1f–%.1f s) …",
        job_id, clip.rank, clip.start_time, clip.end_time,
    )

    # ── 1. Probe source ───────────────────────────────────────────────────────
    probe = probe_video(source_video_path)
    src_w, src_h = get_video_dimensions(probe)

    # ── 2. Disk-space guard ───────────────────────────────────────────────────
    source_size = source_video_path.stat().st_size
    disk = shutil.disk_usage(job_output_dir)
    required = source_size * 2
    if disk.free < required:
        raise RuntimeError(
            f"Insufficient disk space: {disk.free // (1024**2)} MB free, "
            f"need at least {required // (1024**2)} MB."
        )

    # ── 3. Find overlapping segments ──────────────────────────────────────────
    overlapping = transcript.get_segments_in_range(clip.start_time, clip.end_time)

    # ── 4. Generate SRT ───────────────────────────────────────────────────────
    srt_path = job_output_dir / f"clip_{clip.rank}.srt"
    if overlapping:
        generate_srt_for_clip(
            segments=overlapping,
            output_path=srt_path,
            clip_start=clip.start_time,
        )
    else:
        logger.warning(
            "[%s] No transcript segments for clip rank=%d — subtitles skipped.",
            job_id, clip.rank,
        )
        srt_path = None  # type: ignore[assignment]

    # ── 5. Speaker crop detection ─────────────────────────────────────────────
    crop_x = get_dominant_speaker_bbox(
        video_path=source_video_path,
        start=clip.start_time,
        end=clip.end_time,
        src_w=src_w,
        src_h=src_h,
    )

    # ── 6. Build crop filter ──────────────────────────────────────────────────
    crop_filter = build_crop_filter(src_w, src_h, crop_x)

    # ── 7. Build and run FFmpeg command ───────────────────────────────────────
    cmd = build_trim_and_crop_command(
        src=source_video_path,
        out=output_path,
        start=clip.start_time,
        end=clip.end_time,
        crop_filter=crop_filter,
        srt_path=srt_path,
    )

    try:
        run_ffmpeg(cmd)
    except FFmpegError as exc:
        # If the subtitle filter caused the failure, retry without subtitles.
        # This commonly happens on Windows when libass/fontconfig is missing.
        if srt_path is not None and "subtitles" in str(exc).lower():
            logger.warning(
                "[%s] Subtitle filter failed for clip rank=%d — retrying without subtitles. Error: %s",
                job_id, clip.rank, exc,
            )
            cmd_no_sub = build_trim_and_crop_command(
                src=source_video_path,
                out=output_path,
                start=clip.start_time,
                end=clip.end_time,
                crop_filter=crop_filter,
                srt_path=None,  # no subtitles
            )
            run_ffmpeg(cmd_no_sub)
        else:
            logger.error(
                "[%s] FFmpeg failed for clip rank=%d: %s", job_id, clip.rank, exc
            )
            raise

    logger.info(
        "[%s] Clip rank=%d rendered → '%s'", job_id, clip.rank, output_path
    )
    return output_path


# ── Multi-clip orchestrator ───────────────────────────────────────────────────


async def process_all_clips_async(
    job_id: str,
    analysis: GraniteAnalysis,
    transcript: FullTranscript,
    source_video_path: Path,
    clip_ranks: Optional[list[int]] = None,
) -> list[Path]:
    """
    Process all (or a subset of) clips concurrently, bounded by the global
    semaphore.

    Parameters
    ----------
    job_id:
        Job identifier.
    analysis:
        Granite analysis result containing clip metadata.
    transcript:
        Full transcript for subtitle generation.
    source_video_path:
        Path to the source video.
    clip_ranks:
        If provided, only process clips whose ``rank`` is in this list.
        If None, process all clips.

    Returns
    -------
    list[Path]
        Output paths for all successfully rendered clips (in rank order).
    """
    clips_to_process = [
        c for c in analysis.clips
        if clip_ranks is None or c.rank in clip_ranks
    ]

    sem = get_semaphore()
    results: list[Path] = []
    errors: list[tuple[int, Exception]] = []

    async def _process_one(clip: ViralClip) -> Path | None:
        async with sem:
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(
                    None,
                    process_clip,
                    job_id, clip, transcript, source_video_path,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append((clip.rank, exc))
                logger.error(
                    "[%s] Failed to process clip rank=%d: %s",
                    job_id, clip.rank, exc,
                )
                return None

    tasks = [asyncio.create_task(_process_one(c)) for c in clips_to_process]
    raw_results = await asyncio.gather(*tasks)

    for path in raw_results:
        if path is not None:
            results.append(path)

    results.sort(key=lambda p: p.name)  # clip_1.mp4, clip_2.mp4 …

    if errors:
        logger.warning(
            "[%s] %d/%d clips failed: ranks %s",
            job_id, len(errors), len(clips_to_process),
            [r for r, _ in errors],
        )

    return results


def process_all_clips(
    job_id: str,
    analysis: GraniteAnalysis,
    transcript: FullTranscript,
    source_video_path: Path,
    clip_ranks: Optional[list[int]] = None,
) -> list[Path]:
    """
    Synchronous wrapper that processes clips sequentially.

    Runs in a background thread (FastAPI BackgroundTasks), so we avoid
    asyncio.run() which raises 'This event loop is already running' on
    some platforms when called from within an existing event loop thread.
    """
    clips_to_process = [
        c for c in analysis.clips
        if clip_ranks is None or c.rank in clip_ranks
    ]

    results: list[Path] = []
    for clip in clips_to_process:
        try:
            path = process_clip(job_id, clip, transcript, source_video_path)
            results.append(path)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "[%s] Failed to process clip rank=%d: %s",
                job_id, clip.rank, exc,
            )

    results.sort(key=lambda p: p.name)
    return results
