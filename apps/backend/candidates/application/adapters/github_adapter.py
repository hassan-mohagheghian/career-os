"""GitHub source adapter — stub.

A real GitHub adapter would pull repositories / contributions from the GitHub
API. Not wired yet: ``fetch()`` always returns None.
"""

from __future__ import annotations

from candidates.application.adapters.base import CandidateSourceAdapter, SourceContent


class GitHubAdapter(CandidateSourceAdapter):
    """Stub adapter for the GitHub source (unavailable)."""

    source_type = "github"

    def __init__(self, source_repo=None, profile_id=None):
        self._source_repo = source_repo
        self._profile_id = profile_id

    def fetch(self) -> SourceContent | None:
        return None
