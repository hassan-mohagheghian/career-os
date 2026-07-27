"""Career insight repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ICareerInsightRepository(ABC):
    """Interface for career insight data access."""

    @abstractmethod
    def get_all(self) -> dict[str, Any]:
        """Get all insights keyed by insight_type."""
        ...

    @abstractmethod
    def get_section(self, section: str) -> dict[str, Any] | None:
        """Get a specific insight section."""
        ...

    @abstractmethod
    def upsert(self, section: str, data: dict[str, Any], version: int = 1, score: float | None = None, summary: str | None = None) -> None:
        """Insert or update an insight section."""
        ...

    @abstractmethod
    def delete_all(self) -> int:
        """Delete all insights. Returns count deleted."""
        ...
