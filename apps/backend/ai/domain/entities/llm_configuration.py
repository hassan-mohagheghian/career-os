from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Optional

from shared.domain.entity import BaseEntity


class LLMConfiguration(BaseEntity):
    def __init__(
        self,
        id: str | None = None,
        name: str = "",
        model: str = "",
        model_version: str | None = None,
        enabled: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.name = name
        self.model = model
        self.model_version = model_version
        self.enabled = enabled

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def update(self, name: str | None = None, model: str | None = None, model_version: str | None = None, enabled: bool | None = None) -> None:
        if name is not None:
            self.name = name
        if model is not None:
            self.model = model
        if model_version is not None:
            self.model_version = model_version
        if enabled is not None:
            self.enabled = enabled
        self._updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "model_version": self.model_version,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LLMConfiguration:
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            model=data.get("model", ""),
            model_version=data.get("model_version"),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
