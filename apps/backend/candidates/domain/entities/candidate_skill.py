"""CandidateSkill entity — a skill in the candidate profile.

Links to the canonical `skill.skills` vocabulary via a logical `skill_id`
reference (no DB FK) while snapshotting the name/category at extraction time.
Every skill carries provenance (Evidence) and is marked explicit or inferred.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

from candidates.domain._helpers import parse_datetime
from candidates.domain.value_objects.evidence import Evidence

ORIGINS = ("explicit", "inferred")


class CandidateSkill(BaseEntity):
    """A candidate skill with level, confidence, evidence and origin."""

    def __init__(
        self,
        id: str | None = None,
        profile_id: str | None = None,
        skill_id: int | None = None,
        name: str = "",
        level: int = 1,
        category: str = "",
        confidence: float = 0.0,
        origin: str = "explicit",
        years_of_experience: float | None = None,
        last_used: str | None = None,
        evidence: Evidence | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.profile_id = profile_id
        self.skill_id = skill_id
        self.name = name
        self.level = level
        self.category = category
        self.evidence = evidence if evidence is not None else Evidence(confidence=confidence)
        self.origin = origin if origin in ORIGINS else "explicit"
        self.years_of_experience = years_of_experience
        self.last_used = last_used

    @property
    def confidence(self) -> float:
        return self.evidence.confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "skill_id": self.skill_id,
            "name": self.name,
            "level": self.level,
            "category": self.category,
            "confidence": self.evidence.confidence,
            "origin": self.origin,
            "years_of_experience": self.years_of_experience,
            "last_used": self.last_used,
            "evidence": self.evidence.to_dict(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateSkill:
        evidence_data = data.get("evidence") or {}
        if "confidence" not in evidence_data and data.get("confidence") is not None:
            evidence_data = {**evidence_data, "confidence": data.get("confidence")}
        return cls(
            id=data.get("id"),
            profile_id=data.get("profile_id"),
            skill_id=data.get("skill_id"),
            name=data.get("name", ""),
            level=data.get("level", 1),
            category=data.get("category", ""),
            confidence=data.get("confidence", 0.0),
            origin=data.get("origin", "explicit"),
            years_of_experience=data.get("years_of_experience"),
            last_used=data.get("last_used"),
            evidence=Evidence.from_dict(evidence_data),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
