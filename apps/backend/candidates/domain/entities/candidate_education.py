"""CandidateEducation entity — an education entry in the profile."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime
from candidates.domain.value_objects.evidence import Evidence


class CandidateEducation(BaseEntity):
    """An education entry (institution, degree, field)."""

    def __init__(
        self,
        id: str | None = None,
        profile_id: str | None = None,
        institution: str = "",
        degree: str = "",
        field: str = "",
        start_date: str | None = None,
        end_date: str | None = None,
        evidence: Evidence | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.profile_id = profile_id
        self.institution = institution
        self.degree = degree
        self.field = field
        self.start_date = start_date
        self.end_date = end_date
        self.evidence = evidence if evidence is not None else Evidence()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "institution": self.institution,
            "degree": self.degree,
            "field": self.field,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "evidence": self.evidence.to_dict(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateEducation:
        return cls(
            id=data.get("id"),
            profile_id=data.get("profile_id"),
            institution=data.get("institution", ""),
            degree=data.get("degree", ""),
            field=data.get("field", ""),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            evidence=Evidence.from_dict(data.get("evidence")),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
