"""Source adapter contracts for the Candidates context.

Adapters turn raw profile documents (resume, LinkedIn, ...) into a normalized
``SourceContent`` (source type + raw text + source version). The candidates
context owns the ``candidate.candidate_sources`` rows these adapters read;
GitHub/Portfolio adapters are stubs until real providers exist.
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


class CandidateSourceAdapter(ABC):
    """Read the latest available content for a candidate profile source."""

    source_type: str = ""

    @abstractmethod
    def fetch(self) -> SourceContent | None:
        """Return the latest raw content + version, or None when unavailable."""
