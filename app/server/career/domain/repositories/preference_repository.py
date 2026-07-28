"""Preference repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IPreferenceRepository(ABC):
    """Interface for scoring preference/rule data access."""

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """Get all preferences ordered by priority."""
        ...

    @abstractmethod
    def get_by_id(self, pref_id: int) -> dict[str, Any] | None:
        """Get a preference by ID."""
        ...

    @abstractmethod
    def get_enabled_by_scopes(self, scopes: list[str]) -> list[dict[str, Any]]:
        """Get enabled preferences filtered by scope."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new preference."""
        ...

    @abstractmethod
    def update(self, pref_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a preference."""
        ...

    @abstractmethod
    def delete(self, pref_id: int) -> bool:
        """Delete a preference."""
        ...

    @abstractmethod
    def bulk_update(self, items: list[dict[str, Any]]) -> int:
        """Bulk update preferences. Returns count updated."""
        ...
