"""
YouTube video downloader using yt-dlp.
Downloads the best available MP4 (or equivalent) to a local temp directory.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from app.config import settings

# ── URL validation ────────────────────────────────────────────────────────────

_YT_URL_PATTERN = re.compile(
    r"^(https?://)?(www\.)?"
    r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)"
    r"[\w\-]{11}",
    re.IGNORECASE,
)


def _validate_youtube_url(url: str) -> None:
    """Raise ValueError if *url* does not look like a valid YouTube link."""
    if not _YT_URL_PATTERN.match(url):
        raise ValueError(
            f"'{url}' does not appear to be a valid YouTube URL. "
            "Supported formats: youtube.com/watch?v=..., youtu.be/..., "
            "youtube.com/shorts/..."
        )


# ── Downloader ────────────────────────────────────────────────────────────────


def download_youtube_video(url: str, output_dir: Path) -> Path:
    """
    Download a YouTube video to *output_dir* and return its local Path.

    Parameters
    ----------
    url:
        A public YouTube video URL.
    output_dir:
        Directory where the downloaded file will be saved.
        Created automatically if it does not exist.

    Returns
    -------
    Path
        Absolute path to the downloaded video file.

    Raises
    ------
    ValueError
        If the URL format is invalid.
    RuntimeError
        If yt-dlp exits with a non-zero return code (geo-block, private video,
        deleted video, network error, etc.).
    """
    _validate_youtube_url(url)
    output_dir.mkdir(parents=True, exist_ok=True)

    # yt-dlp output template — use a fixed name so we can locate the file
    output_template = str(output_dir / "source.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",            # never download an entire playlist
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--output", output_template,
        "--no-warnings",
        "--quiet",
        url,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,  # 5-minute hard limit for very long videos
    )

    if result.returncode != 0:
        stderr = result.stderr.strip() or "No error details captured."
        raise RuntimeError(
            f"yt-dlp failed (exit {result.returncode}): {stderr}"
        )

    # Locate the downloaded file (extension may vary)
    matches = list(output_dir.glob("source.*"))
    if not matches:
        raise RuntimeError(
            "yt-dlp reported success but no output file was found in "
            f"'{output_dir}'."
        )

    # Prefer .mp4; fall back to whatever yt-dlp produced
    mp4_files = [f for f in matches if f.suffix.lower() == ".mp4"]
    return mp4_files[0] if mp4_files else matches[0]
