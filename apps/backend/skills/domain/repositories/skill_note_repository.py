"""Skill note repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISkillNoteRepository(ABC):
    """Data access for SkillNote rows."""

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_for_skill(self, skill_id: int) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_by_id(self, note_id: int) -> dict[str, Any] | None: ...

    @abstractmethod
    def delete(self, note_id: int) -> bool: ...
