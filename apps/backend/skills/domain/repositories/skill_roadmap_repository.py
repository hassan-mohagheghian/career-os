"""Skill roadmap repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISkillRoadmapRepository(ABC):
    """Interface for skill roadmap data access."""

    @abstractmethod
    def get_by_skill_name(self, skill_name: str) -> list[dict[str, Any]]:
        """Get all roadmap items for a skill."""
        ...

    @abstractmethod
    def get_by_id(self, roadmap_id: int) -> dict[str, Any] | None:
        """Get a roadmap item by ID."""
        ...

    @abstractmethod
    def delete_by_skill_name(self, skill_name: str) -> int:
        """Delete all roadmap items for a skill. Returns count deleted."""
        ...

    @abstractmethod
    def get_max_version(self, skill_name: str) -> int:
        """Get the max version for a skill's roadmap."""
        ...

    @abstractmethod
    def insert_items(self, skill_name: str, items: list[dict[str, Any]], version: int) -> int:
        """Insert roadmap items. Returns count inserted."""
        ...

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """Get all roadmap items ordered by skill_name."""
        ...
