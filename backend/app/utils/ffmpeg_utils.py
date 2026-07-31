"""
FFmpeg command-builder helpers.

All functions that emit shell commands return a plain ``list[str]`` so they
can be passed directly to ``subprocess.run`` without shell=True (safer).

Raises
------
FFmpegError
    Wraps any non-zero exit code or timeout from an FFmpeg subprocess call.
RuntimeError
    Raised at import-time startup check if the configured FFmpeg binary is
    not found on PATH.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


# ── Custom exception ──────────────────────────────────────────────────────────


class FFmpegError(RuntimeError):
    """Raised when an FFmpeg/ffprobe subprocess exits with a non-zero code."""

    def __init__(self, msg: str, returncode: int = -1, stderr: str = "") -> None:
        super().__init__(msg)
        self.returncode = returncode
        self.stderr = stderr


# ── Startup guard ─────────────────────────────────────────────────────────────


def assert_ffmpeg_available() -> None:
    """
    Verify that the configured FFmpeg binary exists on PATH.

    Called once during application startup (``main.py`` lifespan).
    """
    if not shutil.which(settings.ffmpeg_path):
        raise RuntimeError(
            f"FFmpeg binary '{settings.ffmpeg_path}' not found on PATH.\n"
            "Install FFmpeg: https://ffmpeg.org/download.html\n"
            "Then set FFMPEG_PATH in your .env if it is not on PATH."
        )


# ── ffprobe ───────────────────────────────────────────────────────────────────


def probe_video(path: Path) -> dict:
    """
    Run ``ffprobe`` on *path* and return the parsed JSON dict.

    The returned dict contains ``"streams"`` and ``"format"`` keys as
    documented by ffprobe's ``-print_format json`` output.

    Raises
    ------
    FFmpegError
        If ffprobe exits with a non-zero return code.
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the output cannot be parsed as JSON (corrupted / unsupported file).
    """
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {path}")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise FFmpegError(
            f"ffprobe failed on '{path}': {result.stderr.strip()}",
            returncode=result.returncode,
            stderr=result.stderr,
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"ffprobe returned non-JSON output for '{path}': {result.stdout[:200]}"
        ) from exc


def get_video_dimensions(probe_data: dict) -> tuple[int, int]:
    """
    Extract ``(width, height)`` from a ``probe_video()`` result.

    Searches streams for the first video stream.

    Raises
    ------
    ValueError
        If no video stream is found in the probe data.
    """
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "video":
            return int(stream["width"]), int(stream["height"])
    raise ValueError("No video stream found in probe data.")


# ── Audio extraction ──────────────────────────────────────────────────────────


def extract_audio(video_path: Path, output_path: Path) -> None:
    """
    Extract a mono 16 kHz PCM WAV from *video_path* to *output_path*.

    Parameters
    ----------
    video_path:
        Source video file.
    output_path:
        Destination ``.wav`` file path.  Parent directory must exist.

    Raises
    ------
    FFmpegError
        On non-zero exit code.
    """
    cmd = [
        settings.ffmpeg_path,
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_path),
    ]
    run_ffmpeg(cmd, timeout=300)


# ── Crop filter builder ───────────────────────────────────────────────────────


def build_crop_filter(src_w: int, src_h: int, crop_x: int) -> str:
    """
    Build an FFmpeg ``-vf`` crop+scale filter string for 9:16 reframing.

    Parameters
    ----------
    src_w:
        Source video width in pixels.
    src_h:
        Source video height in pixels.
    crop_x:
        Horizontal pixel offset for the crop region (left edge).

    Returns
    -------
    str
        FFmpeg filtergraph string, e.g.
        ``"crop=608:1080:156:0,scale=1080:1920"``.

    Notes
    -----
    * Target crop width  = ``src_h * 9 // 16``  (maintain 9:16 AR).
    * ``crop_x`` is clamped so the crop region never exceeds the source width.
    * If the source is already portrait (width ≤ target_w), returns a
      scale-only filter so we never upscale horizontally.
    """
    target_w = src_h * 9 // 16

    if src_w <= target_w:
        # Already portrait — just scale to 1080×1920
        return "scale=1080:1920:flags=lanczos"

    # Clamp crop_x so the crop box fits inside the frame
    max_crop_x = src_w - target_w
    safe_crop_x = max(0, min(int(crop_x), max_crop_x))

    return f"crop={target_w}:{src_h}:{safe_crop_x}:0,scale=1080:1920:flags=lanczos"


# ── Full trim-crop-subtitle command ──────────────────────────────────────────


def build_trim_and_crop_command(
    src: Path,
    out: Path,
    start: float,
    end: float,
    crop_filter: str,
    srt_path: Path | None = None,
) -> list[str]:
    """
    Assemble the full FFmpeg argument list to trim, crop, optionally burn
    subtitles, and encode to H.264/AAC.

    Parameters
    ----------
    src:
        Source video path.
    out:
        Output clip path (will be overwritten if it exists).
    start:
        Clip start time in seconds.
    end:
        Clip end time in seconds.
    crop_filter:
        The ``-vf`` filtergraph string from :func:`build_crop_filter`.
    srt_path:
        Optional path to an ``.srt`` subtitle file.  If provided, the
        ``subtitles=`` filter is appended to *crop_filter*.

    Returns
    -------
    list[str]
        Argument list ready for ``subprocess.run``.
    """
    vf = crop_filter
    if srt_path is not None and srt_path.exists():
        import platform as _platform
        srt_str = str(srt_path)
        if _platform.system() == "Windows":
            # On Windows: C:\path\to\file.srt → C\:/path/to/file.srt
            # FFmpeg filter syntax requires forward slashes and escaped colons,
            # but the drive-letter colon must stay as \: not be removed.
            srt_str = srt_str.replace("\\", "/")
            # Re-escape the drive-letter colon (e.g. "C:" → "C\:")
            if len(srt_str) >= 2 and srt_str[1] == ":":
                srt_str = srt_str[0] + "\\:" + srt_str[2:]
        vf = f"{vf},subtitles='{srt_str}':force_style='FontSize=14,Bold=1,Alignment=2'"

    cmd = [
        settings.ffmpeg_path,
        "-y",
        "-ss", str(start),
        "-to", str(end),
        "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(out),
    ]
    return cmd


# ── Runner ────────────────────────────────────────────────────────────────────


def run_ffmpeg(cmd: list[str], timeout: int | None = None) -> None:
    """
    Execute an FFmpeg command list as a subprocess.

    Parameters
    ----------
    cmd:
        Full argument list including the ``ffmpeg`` binary at index 0.
    timeout:
        Seconds before the process is killed.  Defaults to
        ``settings.ffmpeg_timeout``.

    Raises
    ------
    FFmpegError
        On non-zero exit code.
    FFmpegError
        On subprocess timeout (returncode = -1).
    """
    effective_timeout = timeout if timeout is not None else settings.ffmpeg_timeout
    logger.debug("Running FFmpeg: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError(
            f"FFmpeg timed out after {effective_timeout}s: {' '.join(cmd[:4])}…",
            returncode=-1,
        ) from exc

    if result.returncode != 0:
        raise FFmpegError(
            f"FFmpeg exited with code {result.returncode}: {result.stderr.strip()[-500:]}",
            returncode=result.returncode,
            stderr=result.stderr,
        )
