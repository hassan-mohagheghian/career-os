"""Source adapter registry — build an adapter for a source type.

``resume`` and ``linkedin`` adapters read ``candidate.candidate_sources`` through
the candidate source repository; ``github`` / ``portfolio`` are stubs.
"""

from __future__ import annotations

from typing import Any

from candidates.application.adapters.base import CandidateSourceAdapter
from candidates.application.adapters.github_adapter import GitHubAdapter
from candidates.application.adapters.linkedin_adapter import LinkedInAdapter
from candidates.application.adapters.portfolio_adapter import PortfolioAdapter
from candidates.application.adapters.resume_adapter import ResumeAdapter

_ADAPTERS: dict[str, type[CandidateSourceAdapter]] = {
    "resume": ResumeAdapter,
    "linkedin": LinkedInAdapter,
    "github": GitHubAdapter,
    "portfolio": PortfolioAdapter,
}


def build_adapter(
    source_type: str, source_repo: Any | None = None, profile_id: str | None = None
) -> CandidateSourceAdapter | None:
    """Build the adapter for ``source_type``, or None when unknown."""
    adapter_cls = _ADAPTERS.get(source_type)
    if adapter_cls is None:
        return None
    return adapter_cls(source_repo, profile_id)


__all__ = [
    "CandidateSourceAdapter",
    "ResumeAdapter",
    "LinkedInAdapter",
    "GitHubAdapter",
    "PortfolioAdapter",
    "build_adapter",
]
