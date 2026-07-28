"""Pending generation repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IPendingGenerationRepository(ABC):
    """Interface for pending generation (resume/cover) data access."""

    @abstractmethod
    def get_by_id(self, gen_id: int) -> dict[str, Any] | None:
        """Get a pending generation by ID."""
        ...

    @abstractmethod
    def create(self, job_num: int, gen_type: str, status: str = "queued") -> dict[str, Any]:
        """Create a new pending generation."""
        ...

    @abstractmethod
    def update_fields(self, gen_id: int, **fields) -> bool:
        """Update fields on a pending generation."""
        ...

    @abstractmethod
    def get_active_for_job(self, job_num: int, gen_type: str) -> dict[str, Any] | None:
        """Get an active (queued/processing) generation for a job."""
        ...

    @abstractmethod
    def get_all_active(self) -> list[dict[str, Any]]:
        """Get all active (queued/processing) generations."""
        ...

    @abstractmethod
    def get_history_for_job(self, job_num: int) -> list[dict[str, Any]]:
        """Get generation history for a specific job."""
        ...

    @abstractmethod
    def get_active_count(self, job_num: int) -> int:
        """Count active generations for a job."""
        ...
