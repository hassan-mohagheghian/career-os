"""CandidateProject entity — a project entry in the profile."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime
from candidates.domain.value_objects.evidence import Evidence


class CandidateProject(BaseEntity):
    """A personal / open-source / professional project."""

    def __init__(
        self,
        id: str | None = None,
        profile_id: str | None = None,
        name: str = "",
        description: str = "",
        url: str = "",
        role: str = "",
        skills: list[str] | None = None,
        evidence: Evidence | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.profile_id = profile_id
        self.name = name
        self.description = description
        self.url = url
        self.role = role
        self.skills = list(skills or [])
        self.evidence = evidence if evidence is not None else Evidence()
        self.start_date = start_date
        self.end_date = end_date

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "role": self.role,
            "skills": list(self.skills),
            "evidence": self.evidence.to_dict(),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateProject:
        return cls(
            id=data.get("id"),
            profile_id=data.get("profile_id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            role=data.get("role", ""),
            skills=data.get("skills") or [],
            evidence=Evidence.from_dict(data.get("evidence")),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
