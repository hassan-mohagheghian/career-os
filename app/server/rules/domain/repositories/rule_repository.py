"""Rule repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IRuleRepository(ABC):
    """Interface for scoring rule data access."""

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """Get all rules ordered by priority."""
        ...

    @abstractmethod
    def get_by_id(self, rule_id: int) -> dict[str, Any] | None:
        """Get a rule by ID."""
        ...

    @abstractmethod
    def get_enabled_by_scopes(self, scopes: list[str]) -> list[dict[str, Any]]:
        """Get enabled rules filtered by scope."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new rule."""
        ...

    @abstractmethod
    def update(self, rule_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a rule."""
        ...

    @abstractmethod
    def delete(self, rule_id: int) -> bool:
        """Delete a rule."""
        ...

    @abstractmethod
    def bulk_update(self, items: list[dict[str, Any]]) -> int:
        """Bulk update rules. Returns count updated."""
        ...
