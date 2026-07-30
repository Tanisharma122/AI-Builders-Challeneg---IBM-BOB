"""
SRT subtitle file generator from Faster-Whisper word-level transcript segments.

Produces standard SubRip (.srt) files with word-grouped subtitle blocks
sized for mobile viewing (≤ max_chars_per_line characters per block).

The "karaoke" effect is achieved by giving each block the timing of its
constituent words rather than the entire segment.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.models.transcript import TranscriptSegment, TranscriptWord

logger = logging.getLogger(__name__)


# ── Time formatting ───────────────────────────────────────────────────────────


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert a float seconds value to SRT timestamp ``HH:MM:SS,mmm``."""
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


# ── Word grouper ──────────────────────────────────────────────────────────────


def _group_words_into_blocks(
    words: list[TranscriptWord],
    max_chars: int,
) -> list[list[TranscriptWord]]:
    """
    Split *words* into blocks where each block's combined text ≤ *max_chars*.

    Returns a list of word-groups.  Each group will become one subtitle block.
    """
    blocks: list[list[TranscriptWord]] = []
    current_block: list[TranscriptWord] = []
    current_len = 0

    for word in words:
        word_text = word.word.strip()
        if not word_text:
            continue  # skip empty tokens

        # +1 for the space between words
        addition = len(word_text) + (1 if current_block else 0)

        if current_block and current_len + addition > max_chars:
            # Flush current block and start a new one
            blocks.append(current_block)
            current_block = [word]
            current_len = len(word_text)
        else:
            current_block.append(word)
            current_len += addition

    if current_block:
        blocks.append(current_block)

    return blocks


# ── SRT writer ────────────────────────────────────────────────────────────────


def generate_srt(
    segment: TranscriptSegment,
    output_path: Path,
    max_chars_per_line: int = 40,
) -> Path:
    """
    Generate an ``.srt`` subtitle file from *segment* and write it to
    *output_path*.

    Parameters
    ----------
    segment:
        A single :class:`~app.models.transcript.TranscriptSegment` containing
        word-level timing.
    output_path:
        Destination path for the ``.srt`` file.  Parent directory is created
        automatically.
    max_chars_per_line:
        Maximum number of characters per subtitle block (default 40).
        Mobile-optimised; set lower for larger font sizes.

    Returns
    -------
    Path
        The path where the ``.srt`` file was written (*output_path*).

    Notes
    -----
    * Falls back to splitting ``segment.text`` into equal chunks when the
      segment has no word-level data (e.g., tiny/base Whisper without
      ``word_timestamps=True``).
    * Blocks with empty text are silently skipped to keep the ``.srt`` valid.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    words = segment.words
    lines: list[str] = []
    seq = 1

    if words:
        blocks = _group_words_into_blocks(words, max_chars_per_line)
        for block in blocks:
            text = " ".join(w.word.strip() for w in block).upper()
            if not text.strip():
                continue
            start_ts = _seconds_to_srt_time(block[0].start_time)
            end_ts = _seconds_to_srt_time(block[-1].end_time)
            lines += [str(seq), f"{start_ts} --> {end_ts}", text, ""]
            seq += 1
    else:
        # Fallback: split segment text evenly across segment duration
        raw_text = segment.text.strip()
        if not raw_text:
            output_path.write_text("", encoding="utf-8")
            return output_path

        words_list = raw_text.split()
        duration = segment.end_time - segment.start_time
        chunk: list[str] = []
        chunk_start = segment.start_time

        for idx, word in enumerate(words_list):
            chunk.append(word)
            chunk_text = " ".join(chunk)
            if len(chunk_text) >= max_chars_per_line or idx == len(words_list) - 1:
                progress = (idx + 1) / len(words_list)
                chunk_end = segment.start_time + duration * progress
                text = chunk_text.upper()
                start_ts = _seconds_to_srt_time(chunk_start)
                end_ts = _seconds_to_srt_time(chunk_end)
                lines += [str(seq), f"{start_ts} --> {end_ts}", text, ""]
                seq += 1
                chunk = []
                chunk_start = chunk_end

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.debug(
        "SRT written to '%s': %d blocks for segment %d.",
        output_path, seq - 1, segment.id,
    )
    return output_path


def generate_srt_for_clip(
    segments: list[TranscriptSegment],
    output_path: Path,
    clip_start: float,
    max_chars_per_line: int = 40,
) -> Path:
    """
    Generate a single merged ``.srt`` for multiple transcript segments
    belonging to one clip.

    Timestamps are made relative to *clip_start* so they align correctly
    when FFmpeg's ``subtitles=`` filter applies them to the trimmed clip.

    Parameters
    ----------
    segments:
        Ordered list of segments overlapping the clip window.
    output_path:
        Destination ``.srt`` path.
    clip_start:
        The clip's ``start_time`` in the original video (used to offset
        subtitle timestamps).
    max_chars_per_line:
        Character budget per subtitle block.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    seq = 1

    for seg in segments:
        words = seg.words
        if words:
            blocks = _group_words_into_blocks(words, max_chars_per_line)
            for block in blocks:
                text = " ".join(w.word.strip() for w in block).upper()
                if not text.strip():
                    continue
                start_ts = _seconds_to_srt_time(
                    max(0.0, block[0].start_time - clip_start)
                )
                end_ts = _seconds_to_srt_time(
                    max(0.0, block[-1].end_time - clip_start)
                )
                lines += [str(seq), f"{start_ts} --> {end_ts}", text, ""]
                seq += 1
        else:
            raw_text = seg.text.strip()
            if not raw_text:
                continue
            start_ts = _seconds_to_srt_time(max(0.0, seg.start_time - clip_start))
            end_ts = _seconds_to_srt_time(max(0.0, seg.end_time - clip_start))
            text = raw_text.upper()
            lines += [str(seq), f"{start_ts} --> {end_ts}", text, ""]
            seq += 1

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.debug(
        "Merged SRT written to '%s': %d blocks across %d segments.",
        output_path, seq - 1, len(segments),
    )
    return output_path
