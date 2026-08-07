"""CandidateProfileVersion entity — an immutable snapshot of a profile.

Every merge produces a new version, preserving traceability of how the
candidate profile evolved over time (Resume V1 → Profile V1, Resume V2 →
Profile V2, ...).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime


class CandidateProfileVersion(BaseEntity):
    """An immutable snapshot of a candidate profile at a version."""

    def __init__(
        self,
        id: str | None = None,
        profile_id: str | None = None,
        version: int = 1,
        snapshot: dict[str, Any] | None = None,
        source_versions: dict[str, int] | None = None,
        change_summary: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.profile_id = profile_id
        self.version = version
        self.snapshot = dict(snapshot or {})
        self.source_versions = dict(source_versions or {})
        self.change_summary = change_summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "version": self.version,
            "snapshot": dict(self.snapshot),
            "source_versions": dict(self.source_versions),
            "change_summary": self.change_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateProfileVersion:
        return cls(
            id=data.get("id"),
            profile_id=data.get("profile_id"),
            version=data.get("version", 1),
            snapshot=data.get("snapshot") or {},
            source_versions=data.get("source_versions") or {},
            change_summary=data.get("change_summary", ""),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
