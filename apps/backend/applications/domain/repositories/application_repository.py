"""Application repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IApplicationRepository(ABC):
    """Data access for the Application aggregate."""

    @abstractmethod
    def get_by_id(self, application_id: str) -> dict[str, Any] | None:
        """Get an application by id, or None."""
        ...

    @abstractmethod
    def get_by_job_id(self, job_id: str) -> dict[str, Any] | None:
        """Get the application for a job, or None."""
        ...

    @abstractmethod
    def list_ids_by_job(self, job_id: str) -> list[str]:
        """List application ids belonging to a job (used by the delete cascade)."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create an application. Returns the stored dict."""
        ...

    @abstractmethod
    def update(self, application_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update application core fields (status, applied_at)."""
        ...

    @abstractmethod
    def delete_by_job(self, job_id: str) -> int:
        """Delete every application (and children) belonging to a job.

        Used by the job hard-delete cascade. Returns the number of applications
        deleted.
        """
        ...
