"""Job analysis repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IJobAnalysisRepository(ABC):
    """Interface for the canonical job analysis data access."""

    @abstractmethod
    def get_by_job_id(self, job_id: str) -> dict[str, Any] | None:
        """Get the analysis for a job, or None if it does not exist."""
        ...

    @abstractmethod
    def upsert_by_job_id(self, job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Insert or update the analysis for a job. Returns the stored dict."""
        ...

    @abstractmethod
    def delete_by_job_id(self, job_id: str) -> bool:
        """Delete the analysis for a job. Returns True if something was deleted."""
        ...

    @abstractmethod
    def recommendations_by_job_ids(self, job_ids: list[str]) -> dict[str, str]:
        """Return a {job_id: recommendation} map for the given job ids (non-null only)."""
        ...
