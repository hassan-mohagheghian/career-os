"""CandidateSource entity — a raw profile source linked to a candidate profile.

Each source has its own independent version (e.g. Resume v4, LinkedIn v3) so
updating one source never requires reprocessing another.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime

SOURCE_TYPES = (
    "resume",
    "linkedin",
    "github",
    "portfolio",
    "stackoverflow",
    "kaggle",
    "behance",
    "dribbble",
    "website",
)

SOURCE_STATUSES = ("pending", "processed", "failed")


class CandidateSource(BaseEntity):
    """A source (resume, LinkedIn, ...) attached to a profile."""

    def __init__(
        self,
        id: str | None = None,
        profile_id: str | None = None,
        source_type: str = "",
        version: int = 1,
        status: str = "pending",
        error: str = "",
        processed_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.profile_id = profile_id
        self.source_type = source_type
        self.version = version
        self.status = status if status in SOURCE_STATUSES else "pending"
        self.error = error
        self.processed_at = processed_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "source_type": self.source_type,
            "version": self.version,
            "status": self.status,
            "error": self.error,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateSource:
        return cls(
            id=data.get("id"),
            profile_id=data.get("profile_id"),
            source_type=data.get("source_type", ""),
            version=data.get("version", 1),
            status=data.get("status", "pending"),
            error=data.get("error", ""),
            processed_at=parse_datetime(data.get("processed_at")),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
