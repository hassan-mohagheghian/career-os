"""CandidateProfile entity — the canonical aggregate root.

The profile is the single source of truth for candidate intelligence. It owns
the core facts and all profile children (skills, experience, projects, ...).
The current version number tracks the latest merge; historical snapshots live
in CandidateProfileVersion.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime


class CandidateProfile(BaseEntity):
    """Aggregate root for the canonical candidate profile."""

    def __init__(
        self,
        id: str | None = None,
        candidate_id: str | None = None,
        version: int = 1,
        name: str = "",
        title: str = "",
        headline: str = "",
        summary: str = "",
        location: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.candidate_id = candidate_id
        self.version = version
        self.name = name
        self.title = title
        self.headline = headline
        self.summary = summary
        self.location = location

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "version": self.version,
            "name": self.name,
            "title": self.title,
            "headline": self.headline,
            "summary": self.summary,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateProfile:
        return cls(
            id=data.get("id"),
            candidate_id=data.get("candidate_id"),
            version=data.get("version", 1),
            name=data.get("name", ""),
            title=data.get("title", ""),
            headline=data.get("headline", ""),
            summary=data.get("summary", ""),
            location=data.get("location", ""),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
