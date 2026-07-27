"""Insight repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IInsightRepository(ABC):
    """Interface for career insight data access."""

    @abstractmethod
    def get_all(self) -> dict[str, Any]:
        """Get all insights."""
        ...

    @abstractmethod
    def get_section(self, section: str) -> dict[str, Any] | None:
        """Get a specific insight section."""
        ...

    @abstractmethod
    def get_statuses(self) -> list[dict[str, Any]]:
        """Get section statuses."""
        ...

    @abstractmethod
    def upsert_section(self, section: str, data: dict[str, Any], status: str = "completed") -> None:
        """Insert or update an insight section."""
        ...
