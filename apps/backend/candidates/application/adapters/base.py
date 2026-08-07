"""Source adapter contracts for the Candidates context.

Adapters turn raw profile documents (resume, LinkedIn, ...) into a normalized
``SourceContent`` (source type + raw text + source version). The jobs context
owns the ``job.resumes`` rows these adapters read; GitHub/Portfolio adapters
are stubs until real providers exist.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceContent:
    """Normalized raw content for a single source version."""

    source_type: str
    raw_text: str
    version: int


def latest_for_prefix(rows: list[dict[str, Any]], prefix: str) -> dict[str, Any] | None:
    """Return the highest-version row whose id starts with ``prefix_``."""
    matched = [r for r in rows if str(r.get("id") or "").startswith(f"{prefix}_")]
    if not matched:
        return None
    return max(matched, key=lambda r: r.get("version") or 0)


class CandidateSourceAdapter(ABC):
    """Read the latest available content for a candidate profile source."""

    source_type: str = ""

    @abstractmethod
    def fetch(self) -> SourceContent | None:
        """Return the latest raw content + version, or None when unavailable."""
