"""Pending generation repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IPendingGenerationRepository(ABC):
    """Interface for pending generation (resume/cover) data access."""

    @abstractmethod
    def get_by_id(self, gen_id: int) -> dict[str, Any] | None:
        """Get a pending generation by ID."""

    @abstractmethod
    def create(self, job_id: str, gen_type: str, status: str = "queued") -> dict[str, Any]:
        """Create a new pending generation."""

    @abstractmethod
    def update_fields(self, gen_id: int, **fields) -> bool:
        """Update fields on a pending generation."""

    @abstractmethod
    def get_active_for_job(self, job_id: str, gen_type: str) -> dict[str, Any] | None:
        """Get an active (queued/processing) generation for a job."""

    @abstractmethod
    def get_all_active(self) -> list[dict[str, Any]]:
        """Get all active (queued/processing) generations."""

    @abstractmethod
    def get_all(self, limit: int = 200) -> list[dict[str, Any]]:
        """Get all generations (including completed/failed)."""

    @abstractmethod
    def get_history_for_job(self, job_id: str) -> list[dict[str, Any]]:
        """Get generation history for a specific job."""

    @abstractmethod
    def get_active_count(self, job_id: str) -> int:
        """Count active generations for a job."""
