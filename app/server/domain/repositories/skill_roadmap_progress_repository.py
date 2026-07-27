"""Skill roadmap progress repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISkillRoadmapProgressRepository(ABC):
    """Interface for skill roadmap progress data access."""

    @abstractmethod
    def get_completed_titles(self, skill_name: str) -> list[str]:
        """Get titles of completed roadmap items for a skill."""
        ...

    @abstractmethod
    def get_by_roadmap_id(self, roadmap_id: int) -> dict[str, Any] | None:
        """Get progress for a specific roadmap item."""
        ...

    @abstractmethod
    def toggle(self, roadmap_id: int, skill_name: str) -> dict[str, Any]:
        """Toggle completion status. Returns updated progress."""
        ...

    @abstractmethod
    def set_completed(self, roadmap_id: int, completed: int) -> dict[str, Any]:
        """Set completion status. Returns updated progress."""
        ...

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """Get all progress records."""
        ...

    @abstractmethod
    def get_by_skill(self, skill_name: str) -> dict[str, Any]:
        """Get progress map {roadmap_id: completed} for a skill."""
        ...

    @abstractmethod
    def get_all_aggregated(self) -> dict[str, Any]:
        """Get aggregated progress by skill_name."""
        ...
