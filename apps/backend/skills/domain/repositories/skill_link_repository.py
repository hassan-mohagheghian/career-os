"""Skill link repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISkillLinkRepository(ABC):
    """Data access for SkillLink rows."""

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_for_skill(self, skill_id: int) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_by_id(self, link_id: int) -> dict[str, Any] | None: ...

    @abstractmethod
    def delete(self, link_id: int) -> bool: ...
