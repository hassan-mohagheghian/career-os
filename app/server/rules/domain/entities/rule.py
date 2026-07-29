"""Rule entity — scoring rules and configuration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity


class Rule(BaseEntity):
    """Rule (scoring rule) entity."""

    def __init__(
        self,
        id: int | None = None,
        category: str = "",
        rule_type: str = "job",
        scope: str = "JOB",
        key: str = "",
        value: str = "",
        description: str | None = None,
        priority: int = 0,
        score_weight: int = 0,
        enabled: int = 1,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, updated_at=updated_at)
        self.category = category
        self.rule_type = rule_type
        self.scope = scope
        self.key = key
        self.value = value
        self.description = description
        self.priority = priority
        self.score_weight = score_weight
        self.enabled = enabled

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "rule_type": self.rule_type,
            "scope": self.scope,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "priority": self.priority,
            "score_weight": self.score_weight,
            "enabled": self.enabled,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        return cls(
            id=data.get("id"),
            category=data.get("category", ""),
            rule_type=data.get("rule_type", "job"),
            scope=data.get("scope", "JOB"),
            key=data.get("key", ""),
            value=data.get("value", ""),
            description=data.get("description"),
            priority=data.get("priority", 0),
            score_weight=data.get("score_weight", 0),
            enabled=data.get("enabled", 1),
            updated_at=data.get("updated_at"),
        )
