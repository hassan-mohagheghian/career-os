"""Job repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IJobRepository(ABC):
    """Interface for job data access."""

    @abstractmethod
    def get_by_id(self, uuid: str) -> dict[str, Any] | None:
        """Get a job by its UUID."""
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
    def update_by_id(self, uuid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Partially update a job's core data by UUID. Returns updated job or None."""
        ...

    @abstractmethod
    def delete_by_id(self, uuid: str) -> bool:
        """Hard-delete a job by UUID and related tables. Returns True if deleted."""
        ...

    @abstractmethod
    def mark_deleted(self, job_id: str) -> None:
        """Soft-delete a job."""
        ...

    @abstractmethod
    def mark_rescoring(self, job_id: str, rescoring: bool = True) -> None:
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
    def update_status(self, job_id: str, status: str, **extra: Any) -> bool:
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
    def get_by_url(self, url: str) -> dict[str, Any] | None:
        """Get a job by URL."""
        ...

    @abstractmethod
    def create_job(self, url: str, title: str | None = None, notes: str = "[]", links: str = "[]", source: str = "api") -> dict[str, Any]:
        """Create a new job. Returns the created job."""
        ...

    @abstractmethod
    def update_fields(self, job_id: str, **fields: Any) -> bool:
        """Update arbitrary fields on a job."""
        ...

    @abstractmethod
    def search_jobs_cursor(
        self,
        cursor: str | None = None,
        page_size: int = 25,
        page: int = 1,
        query: str | None = None,
        sort: str = "updated_at",
        order: str = "desc",
        processing_status: str | None = None,
        company_id: int | None = None,
        remote: bool | None = None,
        visa: bool | None = None,
        overall_score_min: int | None = None,
        overall_score_max: int | None = None,
        fit_score_min: int | None = None,
        fit_score_max: int | None = None,
        success_score_min: int | None = None,
        success_score_max: int | None = None,
    ) -> tuple[list[dict[str, Any]], int, str | None, bool]:
        """Search jobs with cursor-based pagination. Returns (items, total, next_cursor, has_more).

        When `cursor` is None, `page` is applied as an offset ((page-1) * page_size)
        so page-based navigation works as advertised by the API.
        """
        ...
