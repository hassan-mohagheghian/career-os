"""CandidateLanguage entity — a language known by the candidate."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime

PROFICIENCIES = ("basic", "conversational", "professional", "fluent", "native")


class CandidateLanguage(BaseEntity):
    """A language with a proficiency level."""

    def __init__(
        self,
        id: str | None = None,
        profile_id: str | None = None,
        name: str = "",
        proficiency: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.profile_id = profile_id
        self.name = name
        self.proficiency = proficiency if proficiency in PROFICIENCIES else ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "name": self.name,
            "proficiency": self.proficiency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateLanguage:
        return cls(
            id=data.get("id"),
            profile_id=data.get("profile_id"),
            name=data.get("name", ""),
            proficiency=data.get("proficiency", ""),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
