"""Job repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IJobRepository(ABC):
    """Interface for job data access."""

    @abstractmethod
    def get_by_num(self, num: int) -> dict[str, Any] | None:
        """Get a job by its number."""
        ...

    @abstractmethod
    def list_jobs(
        self,
        offset: int | None = None,
        limit: int | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """List jobs with pagination and filtering. Returns (items, total)."""
        ...

    @abstractmethod
    def get_stats(self) -> dict[str, int]:
        """Get aggregate job statistics."""
        ...

    @abstractmethod
    def update(self, num: int, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a job. Returns updated job or None."""
        ...

    @abstractmethod
    def delete(self, num: int) -> bool:
        """Delete a job and related data. Returns True if deleted."""
        ...

    @abstractmethod
    def mark_deleted(self, num: int) -> None:
        """Soft-delete a job."""
        ...

    @abstractmethod
    def mark_rescoring(self, num: int, rescoring: bool = True) -> None:
        """Set or clear the rescoring flag."""
        ...

    @abstractmethod
    def get_all_active(self) -> list[dict[str, Any]]:
        """Get all non-deleted jobs."""
        ...

    @abstractmethod
    def list_by_status(self, status: str) -> list[dict[str, Any]]:
        """List jobs by lifecycle status."""
        ...

    @abstractmethod
    def get_processing_count(self) -> int:
        """Count jobs currently in processing status."""
        ...

    @abstractmethod
    def get_queued_count(self) -> int:
        """Count jobs in queued status."""
        ...

    @abstractmethod
    def update_status(self, num: int, status: str, **extra: Any) -> bool:
        """Update job status and optional extra fields."""
        ...

    @abstractmethod
    def pick_queued_item(self) -> dict[str, Any] | None:
        """Pick the oldest queued job and claim it (set to processing). Returns item or None."""
        ...

    @abstractmethod
    def get_processing_items(self) -> list[dict[str, Any]]:
        """Get all currently processing jobs."""
        ...

    @abstractmethod
    def update_fields(self, num: int, **fields: Any) -> bool:
        """Update arbitrary fields on a job."""
        ...
