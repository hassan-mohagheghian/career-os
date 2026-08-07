"""LinkedIn source adapter — reads the latest LinkedIn profile from ``job.resumes``.

LinkedIn rows are stored with ids like ``linkedin_1``, ``linkedin_2`` in the
jobs context (same table the ``/api/linkedin`` endpoint uses). Cross-context
read only.
"""

from __future__ import annotations

from jobs.domain.repositories.resume_repository import IResumeRepository

from candidates.application.adapters.base import (
    CandidateSourceAdapter,
    SourceContent,
    latest_for_prefix,
)

PREFIX = "linkedin"


class LinkedInAdapter(CandidateSourceAdapter):
    """Adapter for the LinkedIn profile source."""

    source_type = "linkedin"

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
