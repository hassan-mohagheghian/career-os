"""Repository port for the Placeholders bounded context."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IPlaceholderRepository(ABC):
    """Persistence port for named placeholder values."""

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """Return every placeholder, ordered by key."""

    @abstractmethod
    def get_by_key(self, key: str) -> dict[str, Any] | None:
        """Return a single placeholder by key, or None."""

    @abstractmethod
    def upsert(self, key: str, value: str) -> dict[str, Any]:
        """Insert or update a placeholder value (idempotent by key)."""


__all__ = ["IPlaceholderRepository"]