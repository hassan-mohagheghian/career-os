"""CandidateCertificate entity — a certification in the profile."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime
from candidates.domain.value_objects.evidence import Evidence


class CandidateCertificate(BaseEntity):
    """A certification / credential entry."""

    def __init__(
        self,
        id: str | None = None,
        profile_id: str | None = None,
        name: str = "",
        issuer: str = "",
        issue_date: str | None = None,
        credential_url: str = "",
        evidence: Evidence | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.profile_id = profile_id
        self.name = name
        self.issuer = issuer
        self.issue_date = issue_date
        self.credential_url = credential_url
        self.evidence = evidence if evidence is not None else Evidence()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "name": self.name,
            "issuer": self.issuer,
            "issue_date": self.issue_date,
            "credential_url": self.credential_url,
            "evidence": self.evidence.to_dict(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateCertificate:
        return cls(
            id=data.get("id"),
            profile_id=data.get("profile_id"),
            name=data.get("name", ""),
            issuer=data.get("issuer", ""),
            issue_date=data.get("issue_date"),
            credential_url=data.get("credential_url", ""),
            evidence=Evidence.from_dict(data.get("evidence")),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
