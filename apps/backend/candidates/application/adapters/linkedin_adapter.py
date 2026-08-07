"""LinkedIn source adapter — reads the latest LinkedIn profile from candidate_sources.

LinkedIn rows are stored with ``source_type="linkedin"`` in the candidate
context. This adapter reads through the candidate source repository only.
"""

from __future__ import annotations

from typing import Any

from candidates.application.adapters.base import (
    CandidateSourceAdapter,
    SourceContent,
)


class LinkedInAdapter(CandidateSourceAdapter):
    """Adapter for the LinkedIn profile source."""

    source_type = "linkedin"

    def __init__(self, source_repo: Any | None = None, profile_id: str | None = None):
        self._source_repo = source_repo
        self._profile_id = profile_id

    def fetch(self) -> SourceContent | None:
        if self._source_repo is None or not self._profile_id:
            return None
        latest = self._source_repo.get_latest_by_type(self._profile_id, self.source_type)
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
