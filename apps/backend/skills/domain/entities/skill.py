"""Skill entity — aggregate root for the Skills bounded context."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity


class Skill(BaseEntity):
    """Skill aggregate root."""

    def __init__(
        self,
        id: int | None = None,
        name: str = "",
        level: int = 1,
        ml: str | None = None,
        mc: str | None = None,
        roles: str = "",
        path: str = "",
        source: str = "service",
        hidden: int = 0,
        merged_into: str = "",
        category: str = "",
        categories: list[str] | None = None,
        confidence: float = 0,
        market_relevance: float = 0,
        evidence: str = "[]",
        source_type: str = "service",
        tags: str = "[]",
        created_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at)
        self.name = name
        self.level = level
        self.ml = ml
        self.mc = mc
        self.roles = roles
        self.path = path
        self.source = source
        self.hidden = hidden
        self.merged_into = merged_into
        self.category = category
        self.categories = list(categories or [])
        self.confidence = confidence
        self.market_relevance = market_relevance
        self.evidence = evidence
        self.source_type = source_type
        self.tags = tags

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "ml": self.ml,
            "mc": self.mc,
            "roles": self.roles,
            "path": self.path,
            "source": self.source,
            "hidden": self.hidden,
            "merged_into": self.merged_into,
            "category": self.category,
            "categories": list(self.categories),
            "confidence": self.confidence,
            "market_relevance": self.market_relevance,
            "evidence": self.evidence,
            "source_type": self.source_type,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Skill:
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            level=data.get("level", 1),
            ml=data.get("ml"),
            mc=data.get("mc"),
            roles=data.get("roles", ""),
            path=data.get("path", ""),
            source=data.get("source", "service"),
            hidden=data.get("hidden", 0),
            merged_into=data.get("merged_into", ""),
            category=data.get("category", ""),
            categories=data.get("categories"),
            confidence=data.get("confidence", 0),
            market_relevance=data.get("market_relevance", 0),
            evidence=data.get("evidence", "[]"),
            source_type=data.get("source_type", "service"),
            tags=data.get("tags", "[]"),
            created_at=data.get("created_at"),
        )
