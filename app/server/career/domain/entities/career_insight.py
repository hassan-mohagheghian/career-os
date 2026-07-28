"""CareerInsight entity — aggregate root for the Career bounded context."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity


class CareerInsight(BaseEntity):
    """Career insight — versioned insight data."""

    def __init__(
        self,
        id: int | None = None,
        insight_type: str = "",
        version: int = 1,
        score: float | None = None,
        summary: str | None = None,
        data_json: str = "{}",
        created_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at)
        self.insight_type = insight_type
        self.version = version
        self.score = score
        self.summary = summary
        self.data_json = data_json

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "insight_type": self.insight_type,
            "version": self.version,
            "score": self.score,
            "summary": self.summary,
            "data_json": self.data_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
