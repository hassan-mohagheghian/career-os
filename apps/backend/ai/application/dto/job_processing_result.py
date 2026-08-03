"""JobProcessingResult — DTO for job processing results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobProcessingResult:
    """Result of job processing through the AI workflow graph."""
    success: bool = False
    job_id: str | None = None
    company: str | None = None
    title: str | None = None
    score: str | None = None
    fit_score: int | None = None
    success_score: int | None = None
    overall_score: int | None = None
    extraction: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)
    session_id: str = ""
    stages_completed: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "job_id": self.job_id,
            "company": self.company,
            "title": self.title,
            "score": self.score,
            "fit_score": self.fit_score,
            "success_score": self.success_score,
            "overall_score": self.overall_score,
            "extraction": self.extraction,
            "errors": self.errors,
            "session_id": self.session_id,
            "stages_completed": self.stages_completed,
            "metadata": self.metadata,
        }
