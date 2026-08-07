"""CandidateExperience entity — a work experience entry in the profile."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime
from candidates.domain.value_objects.evidence import Evidence


class CandidateExperience(BaseEntity):
    """A work experience entry (company + role over a period)."""

    def __init__(
        self,
        id: str | None = None,
        profile_id: str | None = None,
        company: str = "",
        role: str = "",
        start_date: str | None = None,
        end_date: str | None = None,
        duration_months: int | None = None,
        summary: str = "",
        highlights: list[str] | None = None,
        skills: list[str] | None = None,
        evidence: Evidence | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.profile_id = profile_id
        self.company = company
        self.role = role
        self.start_date = start_date
        self.end_date = end_date
        self.duration_months = duration_months
        self.summary = summary
        self.highlights = list(highlights or [])
        self.skills = list(skills or [])
        self.evidence = evidence if evidence is not None else Evidence()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "company": self.company,
            "role": self.role,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "duration_months": self.duration_months,
            "summary": self.summary,
            "highlights": list(self.highlights),
            "skills": list(self.skills),
            "evidence": self.evidence.to_dict(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateExperience:
        return cls(
            id=data.get("id"),
            profile_id=data.get("profile_id"),
            company=data.get("company", ""),
            role=data.get("role", ""),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            duration_months=data.get("duration_months"),
            summary=data.get("summary", ""),
            highlights=data.get("highlights") or [],
            skills=data.get("skills") or [],
            evidence=Evidence.from_dict(data.get("evidence")),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
