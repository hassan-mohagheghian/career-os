"""Tech learning repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ITechLearningRepository(ABC):
    """Interface for tech learning data access."""

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """Get all tech learning items ordered by priority."""
        ...

    @abstractmethod
    def get_by_id(self, item_id: int) -> dict[str, Any] | None:
        """Get a tech learning item by ID."""
        ...

    @abstractmethod
    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert or update a tech learning item."""
        ...
