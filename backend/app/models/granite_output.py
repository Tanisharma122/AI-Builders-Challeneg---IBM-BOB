"""
Pydantic models for IBM Granite 3.0 structured analysis output.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class ViralClip(BaseModel):
    """A single viral clip candidate identified by Granite."""

    rank: int
    start_time: float
    end_time: float
    hook_text: str
    script_commentary: str
    virality_score: int
    virality_reasoning: str

    @field_validator("virality_score")
    @classmethod
    def _score_in_range(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError(
                f"virality_score must be between 0 and 100, got {v}"
            )
        return v

    @field_validator("hook_text")
    @classmethod
    def _hook_text_max_length(cls, v: str) -> str:
        if len(v) > 100:
            # Truncate gracefully rather than hard-reject
            return v[:100]
        return v

    @property
    def duration(self) -> float:
        return round(self.end_time - self.start_time, 3)


class GraniteAnalysis(BaseModel):
    """Full analysis result from Granite for one job."""

    job_id: str
    clips: list[ViralClip]
    model_used: str = "ibm-granite/granite-3.0-8b-instruct"
    tokens_used: int = 0

    def get_clip_by_rank(self, rank: int) -> ViralClip | None:
        return next((c for c in self.clips if c.rank == rank), None)
