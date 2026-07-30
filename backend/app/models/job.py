"""
Pydantic models for job lifecycle tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """All possible states a processing job can be in."""

    PENDING = "PENDING"
    TRANSCRIBING = "TRANSCRIBING"
    ANALYZING = "ANALYZING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ProcessingJob(BaseModel):
    """Tracks the full lifecycle of a single video processing job."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    progress_pct: int = Field(default=0, ge=0, le=100)
    error_msg: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Optional metadata populated as the job progresses
    source_filename: Optional[str] = None
    youtube_url: Optional[str] = None
    clip_paths: list[str] = Field(default_factory=list)

    def advance(self, status: JobStatus, progress_pct: int) -> None:
        """Move the job to a new status and update the timestamp."""
        self.status = status
        self.progress_pct = progress_pct
        self.updated_at = datetime.now(timezone.utc)

    def fail(self, error_msg: str) -> None:
        """Mark the job as failed with a descriptive message."""
        self.status = JobStatus.FAILED
        self.error_msg = error_msg
        self.updated_at = datetime.now(timezone.utc)

    def complete(self, clip_paths: list[str]) -> None:
        """Mark the job as complete and record output paths."""
        self.status = JobStatus.COMPLETE
        self.progress_pct = 100
        self.clip_paths = clip_paths
        self.updated_at = datetime.now(timezone.utc)
