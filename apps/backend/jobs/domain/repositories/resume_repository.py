"""Resume repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IResumeRepository(ABC):
    """Interface for resume data access."""

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """Get all resumes ordered by created_at DESC."""
        ...

    @abstractmethod
    def get_by_id(self, resume_id: str) -> dict[str, Any] | None:
        """Get a resume by ID."""
        ...

    @abstractmethod
    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert or update a resume."""
        ...

    @abstractmethod
    def delete_by_id(self, resume_id: str) -> bool:
        """Delete a resume by ID."""
        ...

    @abstractmethod
    def get_latest_original_raw_text(self) -> str | None:
        """Get the latest original resume raw text."""
        ...

    @abstractmethod
    def get_latest_linkedin_raw_text(self) -> str | None:
        """Get the latest LinkedIn resume raw text."""
        ...

    @abstractmethod
    def delete_non_original(self) -> int:
        """Delete all resumes except original. Returns count deleted."""
        ...

    @abstractmethod
    def get_for_job(self, job_num: int) -> dict[str, Any] | None:
        """Get the latest resume for a specific job."""
        ...

    @abstractmethod
    def get_cover_for_job(self, job_num: int) -> dict[str, Any] | None:
        """Get the latest cover letter for a specific job."""
        ...
