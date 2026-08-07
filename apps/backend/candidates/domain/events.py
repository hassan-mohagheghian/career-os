"""Domain events for the Candidates bounded context.

Emitted as the candidate profile evolves: profile created/updated, sources
added/updated, merges completed, versions created and skills inferred.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class CandidateProfileCreated(DomainEvent):
    """A candidate profile was created."""

    profile_id: str = ""
    event_type: str = "candidate.profile.created"


@dataclass(frozen=True)
class CandidateProfileUpdated(DomainEvent):
    """A candidate profile was updated (core facts or children changed)."""

    profile_id: str = ""
    event_type: str = "candidate.profile.updated"


@dataclass(frozen=True)
class CandidateSourceAdded(DomainEvent):
    """A new source was attached to a profile."""

    profile_id: str = ""
    source_type: str = ""
    version: int = 1
    event_type: str = "candidate.source.added"


@dataclass(frozen=True)
class CandidateSourceUpdated(DomainEvent):
    """A source changed state or was re-processed."""

    profile_id: str = ""
    source_type: str = ""
    version: int = 1
    status: str = ""
    event_type: str = "candidate.source.updated"


@dataclass(frozen=True)
class CandidateMergeCompleted(DomainEvent):
    """A source was merged into the canonical profile."""

    profile_id: str = ""
    source_type: str = ""
    version: int = 1
    event_type: str = "candidate.merge.completed"


@dataclass(frozen=True)
class CandidateSourceSkipped(DomainEvent):
    """A source was skipped (already processed, empty, or no content)."""

    profile_id: str = ""
    source_type: str = ""
    version: int = 1
    reason: str = ""
    event_type: str = "candidate.source.skipped"


@dataclass(frozen=True)
class CandidateVersionCreated(DomainEvent):
    """A new profile version snapshot was created."""

    profile_id: str = ""
    version: int = 1
    event_type: str = "candidate.version.created"


@dataclass(frozen=True)
class CandidateSkillInferred(DomainEvent):
    """A skill was inferred (not explicit) from a source."""

    profile_id: str = ""
    skill_id: int | None = None
    skill_name: str = ""
    confidence: float = 0.0
    event_type: str = "candidate.skill.inferred"


__all__ = [
    "CandidateProfileCreated",
    "CandidateProfileUpdated",
    "CandidateSourceAdded",
    "CandidateSourceUpdated",
    "CandidateMergeCompleted",
    "CandidateSourceSkipped",
    "CandidateVersionCreated",
    "CandidateSkillInferred",
]
