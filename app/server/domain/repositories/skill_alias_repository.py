"""Skill alias repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISkillAliasRepository(ABC):
    """Interface for skill alias data access."""

    @abstractmethod
    def get_by_skill_id(self, skill_id: int) -> list[dict[str, Any]]:
        """Get all aliases for a skill."""
        ...

    @abstractmethod
    def resolve_name(self, alias_name: str) -> dict[str, Any] | None:
        """Resolve an alias name to its canonical skill."""
        ...

    @abstractmethod
    def create(self, skill_id: int, alias_name: str, normalized_name: str = "") -> dict[str, Any]:
        """Create a new alias."""
        ...

    @abstractmethod
    def exists(self, skill_id: int, alias_name: str) -> bool:
        """Check if an alias exists."""
        ...

    @abstractmethod
    def delete_by_skill_id(self, skill_id: int) -> int:
        """Delete all aliases for a skill. Returns count deleted."""
        ...
