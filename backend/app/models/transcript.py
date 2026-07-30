"""
Pydantic models representing a Faster-Whisper word-level transcript.
"""

from pydantic import BaseModel, field_validator


class TranscriptWord(BaseModel):
    """A single word with its timing and confidence probability."""

    word: str
    start_time: float
    end_time: float
    probability: float

    @field_validator("probability")
    @classmethod
    def _clamp_probability(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    @field_validator("end_time")
    @classmethod
    def _end_after_start(cls, v: float, info) -> float:
        start = info.data.get("start_time")
        if start is not None and v < start:
            raise ValueError(
                f"end_time ({v}) must be >= start_time ({start})"
            )
        return v


class TranscriptSegment(BaseModel):
    """A contiguous speech segment containing one or more words."""

    id: int
    text: str
    start_time: float
    end_time: float
    words: list[TranscriptWord] = []

    @field_validator("end_time")
    @classmethod
    def _end_after_start(cls, v: float, info) -> float:
        start = info.data.get("start_time")
        if start is not None and v < start:
            raise ValueError(
                f"Segment end_time ({v}) must be >= start_time ({start})"
            )
        return v


class FullTranscript(BaseModel):
    """Complete transcript for a video, composed of ordered segments."""

    job_id: str
    language: str
    duration: float
    segments: list[TranscriptSegment] = []

    def get_segments_in_range(
        self, start: float, end: float
    ) -> list[TranscriptSegment]:
        """Return all segments that overlap with [start, end]."""
        return [
            s
            for s in self.segments
            if s.end_time >= start and s.start_time <= end
        ]

    def to_plain_text(self) -> str:
        """Return the full transcript as a single string."""
        return " ".join(s.text.strip() for s in self.segments)
