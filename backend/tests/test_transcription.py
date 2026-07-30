"""
Unit and integration tests for the transcription pipeline.

Run with:
    pytest backend/tests/test_transcription.py -v

The tests use a 10-second synthetic WAV fixture generated at runtime
so the suite has no binary file dependencies and works in CI without
any external downloads.
"""

from __future__ import annotations

import json
import struct
import wave
from pathlib import Path

import pytest

from app.models.transcript import FullTranscript, TranscriptSegment, TranscriptWord


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _write_sine_wav(path: Path, duration_s: float = 10.0, sample_rate: int = 16000) -> None:
    """Write a silent (zero-amplitude) WAV file to *path* for test purposes."""
    import math

    n_samples = int(duration_s * sample_rate)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        # Write near-silence (1 LSB amplitude) so Whisper doesn't crash
        data = struct.pack("<" + "h" * n_samples, *[1] * n_samples)
        wf.writeframes(data)


@pytest.fixture(scope="module")
def silent_wav(tmp_path_factory) -> Path:
    """10-second silent WAV fixture."""
    p = tmp_path_factory.mktemp("audio") / "silent_10s.wav"
    _write_sine_wav(p, duration_s=10.0)
    return p


@pytest.fixture
def sample_segment() -> TranscriptSegment:
    """A TranscriptSegment with 5 words for unit tests."""
    words = [
        TranscriptWord(word="Hello", start_time=0.0, end_time=0.5, probability=0.99),
        TranscriptWord(word=" world", start_time=0.5, end_time=1.0, probability=0.98),
        TranscriptWord(word=" this", start_time=1.0, end_time=1.3, probability=0.97),
        TranscriptWord(word=" is", start_time=1.3, end_time=1.5, probability=0.96),
        TranscriptWord(word=" a", start_time=1.5, end_time=1.7, probability=0.95),
    ]
    return TranscriptSegment(
        id=0,
        text="Hello world this is a",
        start_time=0.0,
        end_time=1.7,
        words=words,
    )


@pytest.fixture
def sample_full_transcript(sample_segment) -> FullTranscript:
    """A minimal FullTranscript for model-level tests."""
    return FullTranscript(
        job_id="test-job-001",
        language="en",
        duration=10.0,
        segments=[sample_segment],
    )


# ── Model unit tests ──────────────────────────────────────────────────────────


class TestTranscriptWord:
    def test_valid_word(self):
        w = TranscriptWord(word="hello", start_time=0.0, end_time=0.5, probability=0.9)
        assert w.word == "hello"
        assert w.probability == 0.9

    def test_probability_clamped_above_one(self):
        w = TranscriptWord(word="hi", start_time=0.0, end_time=0.1, probability=1.5)
        assert w.probability == 1.0

    def test_probability_clamped_below_zero(self):
        w = TranscriptWord(word="hi", start_time=0.0, end_time=0.1, probability=-0.1)
        assert w.probability == 0.0

    def test_end_before_start_raises(self):
        with pytest.raises(ValueError, match="end_time"):
            TranscriptWord(word="bad", start_time=1.0, end_time=0.5, probability=0.9)


class TestTranscriptSegment:
    def test_valid_segment(self, sample_segment):
        assert sample_segment.id == 0
        assert len(sample_segment.words) == 5
        assert sample_segment.start_time < sample_segment.end_time

    def test_end_before_start_raises(self):
        with pytest.raises(ValueError, match="end_time"):
            TranscriptSegment(id=1, text="bad", start_time=5.0, end_time=2.0)


class TestFullTranscript:
    def test_segment_count(self, sample_full_transcript):
        assert len(sample_full_transcript.segments) == 1

    def test_get_segments_in_range(self, sample_full_transcript):
        segs = sample_full_transcript.get_segments_in_range(0.0, 2.0)
        assert len(segs) == 1

    def test_get_segments_out_of_range(self, sample_full_transcript):
        segs = sample_full_transcript.get_segments_in_range(5.0, 10.0)
        assert len(segs) == 0

    def test_to_plain_text(self, sample_full_transcript):
        text = sample_full_transcript.to_plain_text()
        assert "Hello" in text

    def test_round_trip_json(self, sample_full_transcript):
        raw = sample_full_transcript.model_dump_json()
        restored = FullTranscript.model_validate_json(raw)
        assert restored.job_id == sample_full_transcript.job_id
        assert len(restored.segments) == 1


# ── Integration test (requires faster-whisper installed) ─────────────────────


@pytest.mark.integration
def test_transcribe_silent_audio_returns_full_transcript(silent_wav, tmp_path):
    """
    Integration test: pass a real WAV file through the transcription pipeline.

    Marks as 'integration' so it can be skipped in fast CI runs:
        pytest -m "not integration"

    Also auto-skips when FFmpeg or faster-whisper are not installed.
    """
    import shutil as _shutil
    if not _shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not on PATH — skipping transcription integration test")

    pytest.importorskip("faster_whisper", reason="faster-whisper not installed")

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    # Patch settings to use tmp dirs
    import app.config as cfg_module
    original_output = cfg_module.settings.output_dir
    cfg_module.settings.output_dir = tmp_path / "outputs"
    cfg_module.settings.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        from app.services.transcription_service import transcribe_video

        # For silent audio Whisper typically returns zero segments — that's fine.
        # We just assert the returned object is a valid FullTranscript.
        result = transcribe_video(silent_wav, job_id="integration-test")

        assert isinstance(result, FullTranscript)
        assert result.job_id == "integration-test"
        # Each segment must have start < end
        for seg in result.segments:
            assert seg.start_time <= seg.end_time, (
                f"Segment {seg.id}: start={seg.start_time} end={seg.end_time}"
            )
        # Transcript JSON must have been written to disk
        transcript_file = tmp_path / "outputs" / "integration-test" / "transcript.json"
        assert transcript_file.exists(), "transcript.json was not written to disk"
        # Verify the JSON is valid
        loaded = json.loads(transcript_file.read_text())
        assert "segments" in loaded
    finally:
        cfg_module.settings.output_dir = original_output
