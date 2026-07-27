"""Skill relationship repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISkillRelationshipRepository(ABC):
    """Interface for skill relationship data access."""

    @abstractmethod
    def get_for_skill(self, skill_name: str) -> list[dict[str, Any]]:
        """Get all relationships for a skill (as skill_name or related_name)."""
        ...

    @abstractmethod
    def exists(self, skill_name: str, related_name: str, relation_type: str) -> bool:
        """Check if a relationship exists."""
        ...

    @abstractmethod
    def create(self, skill_name: str, related_name: str, relation_type: str, confidence: float = 0) -> bool:
        """Create a relationship. Returns False if already exists."""
        ...

    @abstractmethod
    def delete(self, rel_id: int) -> bool:
        """Delete a relationship by ID."""
        ...

    @abstractmethod
    def delete_all(self) -> int:
        """Delete all relationships. Returns count deleted."""
        ...
