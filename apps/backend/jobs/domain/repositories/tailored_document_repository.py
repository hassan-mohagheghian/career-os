"""TailoredDocument repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ITailoredDocumentRepository(ABC):
    """Interface for tailored document data access."""

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """Get all tailored documents ordered by created_at DESC."""
        ...

    @abstractmethod
    def get_by_id(self, doc_id: str) -> dict[str, Any] | None:
        """Get a tailored document by ID."""
        ...

    @abstractmethod
    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert or update a tailored document."""
        ...

    @abstractmethod
    def delete_by_id(self, doc_id: str) -> bool:
        """Delete a tailored document by ID."""
        ...

    @abstractmethod
    def get_for_job(self, job_id: str) -> dict[str, Any] | None:
        """Get the latest tailored resume for a specific job."""
        ...

    @abstractmethod
    def get_cover_for_job(self, job_id: str) -> dict[str, Any] | None:
        """Get the latest cover letter for a specific job."""
        ...

    @abstractmethod
    def get_active_for_job(self, job_id: str, doc_type: str) -> dict[str, Any] | None:
        """Get an active (in-progress) generation for a job."""
        ...

    @abstractmethod
    def create_generation(self, job_id: str, doc_type: str) -> dict[str, Any]:
        """Create a new generation record for a job."""
        ...

    @abstractmethod
    def get_history_for_job(self, job_id: str) -> list[dict[str, Any]]:
        """Get generation history for a specific job."""
        ...
