"""Resume source adapter — reads the latest master resume from ``job.resumes``.

Resume rows are stored with ids like ``original_1``, ``original_2`` in the jobs
context (same table the ``/api/resumes`` endpoint uses). This adapter is a
cross-context read: it depends on ``IResumeRepository`` and never writes.
"""

from __future__ import annotations

from jobs.domain.repositories.resume_repository import IResumeRepository

from candidates.application.adapters.base import (
    CandidateSourceAdapter,
    SourceContent,
    latest_for_prefix,
)

PREFIX = "original"


class ResumeAdapter(CandidateSourceAdapter):
    """Adapter for the master resume source."""

    source_type = "resume"

    def __init__(self, resume_repo: IResumeRepository | None = None):
        self._resume_repo = resume_repo

    def fetch(self) -> SourceContent | None:
        if self._resume_repo is None:
            return None
        latest = latest_for_prefix(self._resume_repo.get_all(), PREFIX)
        if latest is None:
            return None
        raw_text = latest.get("raw_text")
        if not raw_text or not str(raw_text).strip():
            return None
        return SourceContent(
            source_type=self.source_type,
            raw_text=str(raw_text),
            version=int(latest.get("version") or 1),
        )
