"""Candidate entity — the person the profile belongs to."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime


class Candidate(BaseEntity):
    """The candidate (the user of the platform). A singleton aggregate."""

    def __init__(
        self,
        id: str | None = None,
        name: str = "",
        headline: str = "",
        summary: str = "",
        location: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.name = name
        self.headline = headline
        self.summary = summary
        self.location = location

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "headline": self.headline,
            "summary": self.summary,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Candidate:
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            headline=data.get("headline", ""),
            summary=data.get("summary", ""),
            location=data.get("location", ""),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
