"""
Transcription service using Faster-Whisper with word-level timestamps.

The WhisperModel is loaded once as a lazy module-level singleton to avoid
repeated model loading overhead across multiple requests.
"""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models.transcript import FullTranscript, TranscriptSegment, TranscriptWord

logger = logging.getLogger(__name__)

# ── Lazy singleton ────────────────────────────────────────────────────────────

_model = None  # type: ignore[assignment]


def _get_model():
    """Return the cached WhisperModel, loading it on first call."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel  # type: ignore

        logger.info(
            "Loading Faster-Whisper model '%s' …", settings.whisper_model_size
        )
        _model = WhisperModel(
            settings.whisper_model_size,
            device="cpu",        # use "cuda" if a GPU is available
            compute_type="int8", # int8 is efficient on CPU
        )
        logger.info("Faster-Whisper model loaded.")
    return _model


# ── Audio extraction ──────────────────────────────────────────────────────────


def _extract_audio(video_path: Path, audio_path: Path) -> None:
    """
    Extract a mono 16 kHz WAV from *video_path* using FFmpeg.

    Raises
    ------
    RuntimeError
        If FFmpeg exits with a non-zero return code.
    """
    cmd = [
        settings.ffmpeg_path,
        "-y",                    # overwrite without prompting
        "-i", str(video_path),
        "-vn",                   # no video stream
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(audio_path),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg audio extraction failed: {result.stderr.strip()}"
        )


def _probe_duration(video_path: Path) -> float:
    """Return video duration in seconds via ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        try:
            return float(data["format"]["duration"])
        except (KeyError, ValueError):
            pass
    return 0.0


# ── Core transcription ────────────────────────────────────────────────────────


def transcribe_video(video_path: Path, job_id: str) -> FullTranscript:
    """
    Transcribe *video_path* and return a :class:`FullTranscript`.

    Steps
    -----
    1. Extract mono 16 kHz WAV via FFmpeg.
    2. Run Faster-Whisper with ``word_timestamps=True``.
    3. Map raw segments/words to Pydantic models.
    4. Persist ``transcript.json`` to the job output directory.

    Parameters
    ----------
    video_path:
        Path to the source video file.
    job_id:
        Unique job identifier used for output file naming.

    Returns
    -------
    FullTranscript
        Structured transcript with word-level timestamps.
    """
    job_output_dir = settings.output_dir / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1 — extract audio to a temp WAV
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "audio.wav"
        logger.info("[%s] Extracting audio from '%s' …", job_id, video_path)
        _extract_audio(video_path, audio_path)

        # Step 2 — run Whisper
        model = _get_model()
        logger.info("[%s] Running Whisper transcription …", job_id)
        segments_raw, info = model.transcribe(
            str(audio_path),
            word_timestamps=True,
            beam_size=5,
        )

        detected_language: str = info.language or "en"
        duration: float = info.duration or _probe_duration(video_path)

        # Step 3 — map to Pydantic models
        pydantic_segments: list[TranscriptSegment] = []
        for seg_idx, seg in enumerate(segments_raw):
            words: list[TranscriptWord] = []
            for w in seg.words or []:
                words.append(
                    TranscriptWord(
                        word=w.word,
                        start_time=round(w.start, 3),
                        end_time=round(w.end, 3),
                        probability=round(w.probability, 4),
                    )
                )
            pydantic_segments.append(
                TranscriptSegment(
                    id=seg_idx,
                    text=seg.text.strip(),
                    start_time=round(seg.start, 3),
                    end_time=round(seg.end, 3),
                    words=words,
                )
            )

    transcript = FullTranscript(
        job_id=job_id,
        language=detected_language,
        duration=round(duration, 3),
        segments=pydantic_segments,
    )

    # Step 4 — persist transcript JSON
    transcript_path = job_output_dir / "transcript.json"
    transcript_path.write_text(
        transcript.model_dump_json(indent=2), encoding="utf-8"
    )
    logger.info(
        "[%s] Transcript saved to '%s' (%d segments).",
        job_id,
        transcript_path,
        len(pydantic_segments),
    )

    return transcript


def load_transcript(job_id: str) -> FullTranscript:
    """Load a previously persisted transcript from disk."""
    transcript_path = settings.output_dir / job_id / "transcript.json"
    if not transcript_path.exists():
        raise FileNotFoundError(
            f"No transcript found for job '{job_id}' at '{transcript_path}'."
        )
    return FullTranscript.model_validate_json(
        transcript_path.read_text(encoding="utf-8")
    )
