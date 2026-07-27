"""Skill roadmap job repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISkillRoadmapJobRepository(ABC):
    """Interface for skill roadmap job tracking."""

    @abstractmethod
    def create(self, skill_name: str, job_type: str = "generate", status: str = "queued", **kwargs) -> dict[str, Any]:
        """Create a new roadmap job."""
        ...

    @abstractmethod
    def update(self, job_id: int, **fields) -> bool:
        """Update fields on a roadmap job."""
        ...

    @abstractmethod
    def get_latest_for_skill(self, skill_name: str) -> dict[str, Any] | None:
        """Get the latest job for a skill."""
        ...

    @abstractmethod
    def get_all(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get all roadmap jobs ordered by created_at DESC."""
        ...

    @abstractmethod
    def get_for_skill(self, skill_name: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get jobs for a specific skill."""
        ...
