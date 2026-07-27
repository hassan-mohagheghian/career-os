"""Skill repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISkillRepository(ABC):
    """Interface for skill data access."""

    @abstractmethod
    def list_visible(self, category: str = "") -> list[dict[str, Any]]:
        """Get visible skills with aliases."""
        ...

    @abstractmethod
    def list_hidden(self) -> list[dict[str, Any]]:
        """Get all hidden skills."""
        ...

    @abstractmethod
    def get_by_id(self, skill_id: int) -> dict[str, Any] | None:
        """Get a skill by ID."""
        ...

    @abstractmethod
    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Get a skill by name."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new skill."""
        ...

    @abstractmethod
    def update(self, skill_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a skill."""
        ...

    @abstractmethod
    def delete(self, skill_id: int) -> bool:
        """Delete a skill and its aliases."""
        ...

    @abstractmethod
    def set_hidden(self, skill_id: int, hidden: int) -> dict[str, Any] | None:
        """Set hidden flag on a skill."""
        ...

    @abstractmethod
    def rename(self, skill_id: int, new_name: str) -> dict[str, Any] | None:
        """Rename a skill and update all references."""
        ...

    @abstractmethod
    def merge(self, target_id: int, source_ids: list[int]) -> dict[str, Any]:
        """Merge source skills into target."""
        ...

    @abstractmethod
    def get_categories(self) -> list[dict[str, Any]]:
        """Get all categories with counts."""
        ...

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get overall skill statistics."""
        ...

    @abstractmethod
    def bulk_hide(self, skill_ids: list[int]) -> int:
        """Hide multiple skills. Returns count hidden."""
        ...

    @abstractmethod
    def bulk_categorize(self, skill_ids: list[int], category: str) -> int:
        """Categorize multiple skills. Returns count updated."""
        ...

    @abstractmethod
    def get_relationships(self, skill_name: str) -> list[dict[str, Any]]:
        """Get all relationships for a skill."""
        ...

    @abstractmethod
    def create_relationship(self, data: dict[str, Any]) -> bool:
        """Create a skill relationship. Returns True if created."""
        ...

    @abstractmethod
    def delete_relationship(self, rel_id: int) -> bool:
        """Delete a skill relationship."""
        ...
