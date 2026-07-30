"""
Tests for the Granite analyzer service.

S2-T06 requirements:
- Unit test _validate_and_parse with valid fixture → GraniteAnalysis with ≥1 clip
- Unit test _validate_and_parse with invalid JSON → raises GraniteOutputValidationError
- Mock _call_granite_api to avoid real API calls in CI

Run with:
    pytest backend/tests/test_granite_analyzer.py -v
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.models.granite_output import GraniteAnalysis, ViralClip
from app.models.transcript import FullTranscript, TranscriptSegment, TranscriptWord
from app.services.granite_analyzer import (
    GraniteOutputValidationError,
    _build_prompt,
    _strip_fences,
    _validate_and_parse,
    analyze_transcript,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


VALID_GRANITE_RESPONSE = {
    "clips": [
        {
            "rank": 1,
            "start_time": 10.0,
            "end_time": 70.0,
            "hook_text": "This one trick changed everything",
            "script_commentary": "Strong emotional opener with a clear hook.",
            "virality_score": 88,
            "virality_reasoning": "High shareability, emotional resonance, and surprising reveal.",
        },
        {
            "rank": 2,
            "start_time": 80.0,
            "end_time": 140.0,
            "hook_text": "Nobody talks about this",
            "script_commentary": "Creates curiosity gap effectively.",
            "virality_score": 74,
            "virality_reasoning": "Curiosity-driven hook with clear value proposition.",
        },
        {
            "rank": 3,
            "start_time": 150.0,
            "end_time": 210.0,
            "hook_text": "Wait for the twist at the end",
            "script_commentary": "Retention bait with strong narrative arc.",
            "virality_score": 65,
            "virality_reasoning": "Twist-based retention strategy.",
        },
        {
            "rank": 4,
            "start_time": 220.0,
            "end_time": 280.0,
            "hook_text": "I can't believe this actually works",
            "script_commentary": "Social proof combined with surprise.",
            "virality_score": 60,
            "virality_reasoning": "Relatability and surprise factor.",
        },
        {
            "rank": 5,
            "start_time": 290.0,
            "end_time": 350.0,
            "hook_text": "The secret no one tells you",
            "script_commentary": "Insider knowledge framing.",
            "virality_score": 55,
            "virality_reasoning": "Exclusive information framing drives shares.",
        },
    ]
}


@pytest.fixture
def valid_json_str() -> str:
    return json.dumps(VALID_GRANITE_RESPONSE)


@pytest.fixture
def sample_transcript() -> FullTranscript:
    words = [
        TranscriptWord(word=w, start_time=i * 0.5, end_time=(i + 1) * 0.5, probability=0.95)
        for i, w in enumerate(["Hello", "world", "this", "is", "a", "test"])
    ]
    seg = TranscriptSegment(
        id=0,
        text="Hello world this is a test",
        start_time=0.0,
        end_time=3.0,
        words=words,
    )
    return FullTranscript(
        job_id="test-granite-001",
        language="en",
        duration=400.0,
        segments=[seg],
    )


# ── _strip_fences ─────────────────────────────────────────────────────────────


class TestStripFences:
    def test_strips_json_code_fence(self):
        raw = "```json\n{\"clips\": []}\n```"
        assert _strip_fences(raw) == '{"clips": []}'

    def test_strips_plain_code_fence(self):
        raw = "```\n{\"clips\": []}\n```"
        assert _strip_fences(raw) == '{"clips": []}'

    def test_no_fence_passthrough(self):
        raw = '{"clips": []}'
        assert _strip_fences(raw) == raw

    def test_strips_leading_prose(self):
        raw = 'Here is the JSON:\n{"clips": []}'
        result = _strip_fences(raw)
        assert result.startswith("{")


# ── _validate_and_parse ───────────────────────────────────────────────────────


class TestValidateAndParse:
    def test_valid_response_returns_dict_with_5_clips(self, valid_json_str):
        result = _validate_and_parse(valid_json_str, job_id="test", duration=400.0)
        assert "clips" in result
        assert len(result["clips"]) == 5

    def test_clips_are_clamped_to_duration(self):
        data = {
            "clips": [
                {
                    "rank": 1,
                    "start_time": 500.0,  # beyond duration
                    "end_time": 600.0,
                    "hook_text": "Test hook",
                    "script_commentary": "Test commentary",
                    "virality_score": 50,
                    "virality_reasoning": "Test reasoning",
                }
            ]
        }
        # Both timestamps > duration (100s) → clip duration < 5s → discarded
        result = _validate_and_parse(json.dumps(data), job_id="test", duration=100.0)
        assert result["clips"] == []

    def test_short_clip_is_discarded(self):
        data = {
            "clips": [
                {
                    "rank": 1,
                    "start_time": 10.0,
                    "end_time": 13.0,  # only 3 seconds
                    "hook_text": "Short clip",
                    "script_commentary": "Too short",
                    "virality_score": 50,
                    "virality_reasoning": "Too short",
                }
            ]
        }
        result = _validate_and_parse(json.dumps(data), job_id="test", duration=100.0)
        assert result["clips"] == []

    def test_invalid_json_raises(self):
        with pytest.raises(GraniteOutputValidationError, match="not valid JSON"):
            _validate_and_parse("not json at all {{{", job_id="test", duration=100.0)

    def test_missing_required_field_raises(self):
        data = {"clips": [{"rank": 1}]}  # missing many required fields
        with pytest.raises(GraniteOutputValidationError):
            _validate_and_parse(json.dumps(data), job_id="test", duration=100.0)

    def test_virality_score_out_of_range_raises(self):
        data = {
            "clips": [
                {
                    "rank": 1,
                    "start_time": 10.0,
                    "end_time": 70.0,
                    "hook_text": "Test",
                    "script_commentary": "Test",
                    "virality_score": 150,  # invalid: > 100
                    "virality_reasoning": "Test",
                }
            ]
        }
        with pytest.raises(GraniteOutputValidationError):
            _validate_and_parse(json.dumps(data), job_id="test", duration=100.0)

    def test_response_wrapped_in_fences_is_parsed(self, valid_json_str):
        fenced = f"```json\n{valid_json_str}\n```"
        result = _validate_and_parse(fenced, job_id="test", duration=400.0)
        assert len(result["clips"]) == 5


# ── ViralClip model ───────────────────────────────────────────────────────────


class TestViralClip:
    def test_virality_score_valid(self):
        clip = ViralClip(
            rank=1, start_time=0.0, end_time=60.0,
            hook_text="Hook", script_commentary="Commentary",
            virality_score=75, virality_reasoning="Good"
        )
        assert clip.virality_score == 75

    def test_virality_score_out_of_range(self):
        with pytest.raises(ValueError, match="virality_score"):
            ViralClip(
                rank=1, start_time=0.0, end_time=60.0,
                hook_text="Hook", script_commentary="Commentary",
                virality_score=101, virality_reasoning="Bad"
            )

    def test_hook_text_truncated_at_100(self):
        long_hook = "A" * 150
        clip = ViralClip(
            rank=1, start_time=0.0, end_time=60.0,
            hook_text=long_hook, script_commentary="Commentary",
            virality_score=50, virality_reasoning="Reasoning"
        )
        assert len(clip.hook_text) == 100

    def test_duration_property(self):
        clip = ViralClip(
            rank=1, start_time=10.0, end_time=70.0,
            hook_text="Hook", script_commentary="Commentary",
            virality_score=50, virality_reasoning="Reasoning"
        )
        assert clip.duration == 60.0


# ── _build_prompt ─────────────────────────────────────────────────────────────


class TestBuildPrompt:
    def test_prompt_contains_transcript_text(self, sample_transcript):
        prompt = _build_prompt(sample_transcript)
        assert "Hello world" in prompt

    def test_prompt_instructs_json_only(self, sample_transcript):
        prompt = _build_prompt(sample_transcript)
        assert "JSON" in prompt
        assert "markdown" in prompt.lower() or "fences" in prompt.lower() or "nothing else" in prompt.lower()

    def test_long_transcript_is_truncated(self):
        # Build a very long transcript
        words = [
            TranscriptWord(word=f"word{i}", start_time=i * 0.1, end_time=(i + 1) * 0.1, probability=0.9)
            for i in range(5000)
        ]
        seg = TranscriptSegment(
            id=0, text=" ".join(f"word{i}" for i in range(5000)),
            start_time=0.0, end_time=500.0, words=words
        )
        big_transcript = FullTranscript(
            job_id="big-job", language="en", duration=500.0, segments=[seg]
        )
        prompt = _build_prompt(big_transcript)
        # Prompt must build without error and contain key instructions
        assert "viral" in prompt.lower()
        assert "JSON" in prompt
        assert "Nothing else" in prompt


# ── analyze_transcript (mocked API) ──────────────────────────────────────────


class TestAnalyzeTranscript:
    def test_full_pipeline_with_mocked_api(self, sample_transcript, tmp_path):
        """Full analyze_transcript call with API mocked — no network required."""
        import app.services.granite_analyzer as ga_module
        import app.config as cfg_module

        # Point output dir at tmp_path
        original_output = cfg_module.settings.output_dir
        cfg_module.settings.output_dir = tmp_path
        (tmp_path / sample_transcript.job_id).mkdir(parents=True, exist_ok=True)

        mock_response = json.dumps(VALID_GRANITE_RESPONSE)

        try:
            with patch.object(ga_module, "_call_granite_api", return_value=(mock_response, 512)):
                result = analyze_transcript(sample_transcript, sample_transcript.job_id)

            assert isinstance(result, GraniteAnalysis)
            assert result.job_id == sample_transcript.job_id
            assert len(result.clips) == 5
            assert all(isinstance(c, ViralClip) for c in result.clips)

            # Verify persistence
            analysis_file = tmp_path / sample_transcript.job_id / "granite_analysis.json"
            assert analysis_file.exists()
            loaded = GraniteAnalysis.model_validate_json(analysis_file.read_text())
            assert loaded.job_id == sample_transcript.job_id

        finally:
            cfg_module.settings.output_dir = original_output

    def test_invalid_api_response_raises(self, sample_transcript, tmp_path):
        """When Granite returns garbage, analyze_transcript raises GraniteOutputValidationError."""
        import app.services.granite_analyzer as ga_module
        import app.config as cfg_module

        original_output = cfg_module.settings.output_dir
        cfg_module.settings.output_dir = tmp_path

        try:
            with patch.object(ga_module, "_call_granite_api", return_value=("not json ~~~", 10)):
                with pytest.raises(GraniteOutputValidationError):
                    analyze_transcript(sample_transcript, sample_transcript.job_id)
        finally:
            cfg_module.settings.output_dir = original_output
