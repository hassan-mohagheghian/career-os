"""Portfolio source adapter — stub.

A real portfolio adapter would fetch a personal website / portfolio page. Not
wired yet: ``fetch()`` always returns None.
"""

from __future__ import annotations

from candidates.application.adapters.base import CandidateSourceAdapter, SourceContent


class PortfolioAdapter(CandidateSourceAdapter):
    """Stub adapter for the portfolio source (unavailable)."""

    source_type = "portfolio"

    def __init__(self, resume_repo=None):
        self._resume_repo = resume_repo

    def fetch(self) -> SourceContent | None:
        return None
