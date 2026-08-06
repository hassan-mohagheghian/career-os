"""Job-company repository interface.

Stores the per-job company associations extracted during job processing. Rows
are replaced for a job on re-processing (``replace_for_job``).
"""

from abc import ABC, abstractmethod
from typing import Any


class IJobCompanyRepository(ABC):
    """Interface for job_companies data access."""

    @abstractmethod
    def replace_for_job(self, job_id: str, rows: list[dict[str, Any]]) -> None:
        """Delete all rows for a job, then insert the given rows.

        Each row: ``{company_id, role, company_type, confidence, reason}``.
        """
        ...

    @abstractmethod
    def list_by_job(self, job_id: str) -> list[dict[str, Any]]:
        """List company associations for a job (newest first)."""
        ...

    @abstractmethod
    def list_by_company(self, company_id: str, role: str | None = None) -> list[dict[str, Any]]:
        """List job associations for a company, optionally filtered by role."""
        ...

    @abstractmethod
    def recruiter_hiring_pairs(self, recruiter_id: str) -> list[dict[str, Any]]:
        """For a recruiter company, return the hiring companies of the jobs it
        published: ``[{job_id, hiring_company_id}]`` (one entry per job)."""
        ...
