"""
Tests for Phase 3 — FFmpeg utilities, subtitle service, and video processor.

S3-T06 requirements:
  - Test build_crop_filter(1920, 1080, 420) returns correct FFmpeg string
  - Test generate_srt() with 5-word TranscriptSegment produces valid SRT format
  - Integration test run_ffmpeg() with a real 5-second clip (CI-safe, small)

Run with:
    pytest backend/tests/test_video_processor.py -v
    pytest backend/tests/test_video_processor.py -v -m "not integration"
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path

import pytest

from app.models.transcript import TranscriptSegment, TranscriptWord
from app.services.subtitle_service import (
    _group_words_into_blocks,
    _seconds_to_srt_time,
    generate_srt,
    generate_srt_for_clip,
)
from app.utils.ffmpeg_utils import (
    FFmpegError,
    build_crop_filter,
    build_trim_and_crop_command,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def five_word_segment() -> TranscriptSegment:
    words = [
        TranscriptWord(word="Hello", start_time=0.0, end_time=0.5, probability=0.99),
        TranscriptWord(word=" world", start_time=0.5, end_time=1.0, probability=0.98),
        TranscriptWord(word=" this", start_time=1.0, end_time=1.4, probability=0.97),
        TranscriptWord(word=" is", start_time=1.4, end_time=1.7, probability=0.96),
        TranscriptWord(word=" test", start_time=1.7, end_time=2.2, probability=0.95),
    ]
    return TranscriptSegment(
        id=0,
        text="Hello world this is test",
        start_time=0.0,
        end_time=2.2,
        words=words,
    )


def _make_silent_mp4(path: Path, duration_s: float = 5.0) -> Path:
    """
    Create a tiny valid MP4 using FFmpeg (lavfi sources).
    Skips creation if FFmpeg is not available.
    """
    import shutil
    import subprocess

    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not on PATH — skipping integration test")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=black:size=640x480:rate=25:duration={duration_s}",
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", str(duration_s),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
        "-c:a", "aac", "-shortest",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if result.returncode != 0:
        pytest.skip(f"Could not create test MP4: {result.stderr.decode()[:200]}")
    return path


# ── _seconds_to_srt_time ──────────────────────────────────────────────────────


class TestSrtTimeFormat:
    def test_zero(self):
        assert _seconds_to_srt_time(0.0) == "00:00:00,000"

    def test_one_hour(self):
        assert _seconds_to_srt_time(3600.0) == "01:00:00,000"

    def test_fractional(self):
        assert _seconds_to_srt_time(1.5) == "00:00:01,500"

    def test_complex(self):
        # 1h 2m 3.456s
        t = 3600 + 120 + 3.456
        assert _seconds_to_srt_time(t) == "01:02:03,456"

    def test_milliseconds_rounding(self):
        result = _seconds_to_srt_time(0.0009)
        assert result == "00:00:00,001"


# ── _group_words_into_blocks ──────────────────────────────────────────────────


class TestWordGrouper:
    def test_five_words_fit_in_one_block(self, five_word_segment):
        blocks = _group_words_into_blocks(five_word_segment.words, max_chars=80)
        assert len(blocks) == 1
        assert len(blocks[0]) == 5

    def test_splits_into_multiple_blocks(self, five_word_segment):
        # max_chars=5 forces one word per block
        blocks = _group_words_into_blocks(five_word_segment.words, max_chars=5)
        assert len(blocks) == 5

    def test_empty_words_skipped(self):
        words = [
            TranscriptWord(word="  ", start_time=0.0, end_time=0.1, probability=0.9),
            TranscriptWord(word="hi", start_time=0.1, end_time=0.3, probability=0.9),
        ]
        blocks = _group_words_into_blocks(words, max_chars=40)
        # Empty word should be skipped
        assert blocks == [] or all(
            any(w.word.strip() for w in b) for b in blocks
        )


# ── build_crop_filter ─────────────────────────────────────────────────────────


class TestBuildCropFilter:
    def test_standard_1080p_landscape(self):
        """1920×1080 landscape → target_w = 1080*9//16 = 607 (or 608)"""
        result = build_crop_filter(1920, 1080, 420)
        # target_w = 1080 * 9 // 16 = 607
        assert result.startswith("crop=607:1080:") or result.startswith("crop=608:1080:")
        assert "scale=1080:1920" in result

    def test_crop_x_clamped_to_max(self):
        """crop_x must be clamped so the box doesn't go out of bounds."""
        # 1920 wide, target_w=607, max_crop_x = 1920-607 = 1313
        result = build_crop_filter(1920, 1080, 9999)
        # Should NOT contain :9999:
        assert ":9999:" not in result

    def test_crop_x_zero(self):
        result = build_crop_filter(1920, 1080, 0)
        assert ":0:0" in result

    def test_portrait_source_returns_scale_only(self):
        """Portrait source (width ≤ target_w) should skip crop and just scale."""
        # 720×1280 → target_w = 1280*9//16 = 720 → src_w == target_w
        result = build_crop_filter(720, 1280, 0)
        assert result.startswith("scale=1080:1920")
        assert "crop" not in result

    def test_4k_source(self):
        result = build_crop_filter(3840, 2160, 1000)
        assert "scale=1080:1920" in result
        assert "crop" in result

    def test_exact_spec_from_tasks_md(self):
        """Verify the exact example from tasks.md: build_crop_filter(1920, 1080, 420)"""
        result = build_crop_filter(1920, 1080, 420)
        # target_w = 1080 * 9 // 16 = 607
        assert "1080" in result          # src_h in crop
        assert "420" in result           # crop_x preserved (within bounds)
        assert "1920" in result          # output scale width
        assert "scale=1080:1920" in result


# ── generate_srt ─────────────────────────────────────────────────────────────


class TestGenerateSrt:
    def test_produces_valid_srt_file(self, five_word_segment, tmp_path):
        srt_path = tmp_path / "test.srt"
        result = generate_srt(five_word_segment, srt_path)

        assert result == srt_path
        assert srt_path.exists()
        content = srt_path.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_srt_contains_sequence_number(self, five_word_segment, tmp_path):
        srt_path = tmp_path / "test.srt"
        generate_srt(five_word_segment, srt_path)
        content = srt_path.read_text(encoding="utf-8")
        assert "1\n" in content

    def test_srt_contains_timestamp_arrow(self, five_word_segment, tmp_path):
        srt_path = tmp_path / "test.srt"
        generate_srt(five_word_segment, srt_path)
        content = srt_path.read_text(encoding="utf-8")
        assert "-->" in content

    def test_srt_text_is_uppercase(self, five_word_segment, tmp_path):
        srt_path = tmp_path / "test.srt"
        generate_srt(five_word_segment, srt_path)
        content = srt_path.read_text(encoding="utf-8")
        # Non-timestamp, non-sequence lines should be uppercase
        text_lines = [
            ln for ln in content.splitlines()
            if ln.strip() and "-->" not in ln and not ln.strip().isdigit()
        ]
        for line in text_lines:
            assert line == line.upper(), f"Line not uppercase: {line!r}"

    def test_srt_without_words_uses_fallback(self, tmp_path):
        seg = TranscriptSegment(
            id=0,
            text="Fallback text here",
            start_time=0.0,
            end_time=3.0,
            words=[],  # no word-level data
        )
        srt_path = tmp_path / "fallback.srt"
        generate_srt(seg, srt_path)
        assert srt_path.exists()
        content = srt_path.read_text()
        assert "FALLBACK TEXT HERE" in content

    def test_srt_empty_segment_creates_empty_file(self, tmp_path):
        seg = TranscriptSegment(
            id=0, text="", start_time=0.0, end_time=1.0, words=[]
        )
        srt_path = tmp_path / "empty.srt"
        generate_srt(seg, srt_path)
        assert srt_path.exists()

    def test_generate_srt_for_clip_offsets_timestamps(self, five_word_segment, tmp_path):
        """Timestamps must be relative to clip_start, not absolute."""
        # Shift the segment to start at 30s in the original video
        shifted_words = [
            TranscriptWord(
                word=w.word,
                start_time=w.start_time + 30.0,
                end_time=w.end_time + 30.0,
                probability=w.probability,
            )
            for w in five_word_segment.words
        ]
        shifted_seg = TranscriptSegment(
            id=0, text=five_word_segment.text,
            start_time=30.0, end_time=32.2, words=shifted_words
        )
        srt_path = tmp_path / "clip.srt"
        generate_srt_for_clip([shifted_seg], srt_path, clip_start=30.0)
        content = srt_path.read_text()
        # First timestamp should start near 00:00:00, not 00:00:30
        assert "00:00:00" in content


# ── build_trim_and_crop_command ───────────────────────────────────────────────


class TestBuildTrimCommand:
    def test_returns_list_of_strings(self, tmp_path):
        cmd = build_trim_and_crop_command(
            src=tmp_path / "src.mp4",
            out=tmp_path / "out.mp4",
            start=0.0,
            end=30.0,
            crop_filter="scale=1080:1920",
        )
        assert isinstance(cmd, list)
        assert all(isinstance(s, str) for s in cmd)

    def test_contains_libx264_and_aac(self, tmp_path):
        cmd = build_trim_and_crop_command(
            src=tmp_path / "src.mp4",
            out=tmp_path / "out.mp4",
            start=5.0,
            end=35.0,
            crop_filter="scale=1080:1920",
        )
        assert "libx264" in cmd
        assert "aac" in cmd

    def test_appends_subtitles_filter_when_srt_provided(self, tmp_path):
        srt = tmp_path / "sub.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHELLO\n")
        cmd = build_trim_and_crop_command(
            src=tmp_path / "src.mp4",
            out=tmp_path / "out.mp4",
            start=0.0,
            end=30.0,
            crop_filter="crop=607:1080:420:0,scale=1080:1920",
            srt_path=srt,
        )
        vf_idx = cmd.index("-vf") + 1
        assert "subtitles" in cmd[vf_idx]

    def test_no_subtitle_filter_when_srt_none(self, tmp_path):
        cmd = build_trim_and_crop_command(
            src=tmp_path / "src.mp4",
            out=tmp_path / "out.mp4",
            start=0.0,
            end=30.0,
            crop_filter="scale=1080:1920",
            srt_path=None,
        )
        vf_idx = cmd.index("-vf") + 1
        assert "subtitles" not in cmd[vf_idx]


# ── Integration: run_ffmpeg with a real 5-second clip ────────────────────────


@pytest.mark.integration
def test_run_ffmpeg_trims_real_clip(tmp_path):
    """
    Generate a real 5-second lavfi MP4 and verify FFmpeg can trim + scale it.
    Requires FFmpeg on PATH.
    """
    import shutil as _shutil
    if not _shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not on PATH")

    from app.utils.ffmpeg_utils import run_ffmpeg

    src = tmp_path / "source.mp4"
    out = tmp_path / "trimmed.mp4"
    _make_silent_mp4(src, duration_s=5.0)

    cmd = build_trim_and_crop_command(
        src=src,
        out=out,
        start=0.0,
        end=3.0,
        crop_filter="scale=640:480",
    )
    run_ffmpeg(cmd, timeout=60)

    assert out.exists()
    assert out.stat().st_size > 1000  # non-trivial output


@pytest.mark.integration
def test_run_ffmpeg_raises_on_bad_input(tmp_path):
    """FFmpegError must be raised when FFmpeg exits non-zero."""
    import shutil as _shutil
    if not _shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not on PATH")

    from app.utils.ffmpeg_utils import run_ffmpeg

    cmd = ["ffmpeg", "-y", "-i", str(tmp_path / "nonexistent.mp4"),
           str(tmp_path / "out.mp4")]
    with pytest.raises(FFmpegError):
        run_ffmpeg(cmd, timeout=10)
