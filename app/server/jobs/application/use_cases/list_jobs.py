"""List jobs use case — orchestrates job listing with filtering and pagination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jobs.domain.repositories.job_repository import IJobRepository


@dataclass
class ListJobsRequest:
    """Input DTO for listing jobs."""
    offset: int = 0
    limit: int = 50
    sort_by: str = "created_at"
    sort_dir: str = "desc"
    filters: dict[str, Any] | None = None


@dataclass
class ListJobsResponse:
    """Output DTO for listing jobs."""
    items: list[dict[str, Any]]
    total: int


class ListJobsUseCase:
    """Use case for listing jobs with pagination and filtering."""

    def __init__(self, job_repository: IJobRepository):
        self._job_repository = job_repository

    def execute(self, request: ListJobsRequest) -> ListJobsResponse:
        items, total = self._job_repository.list_jobs(
            offset=request.offset,
            limit=request.limit,
            sort_by=request.sort_by,
            sort_dir=request.sort_dir,
            filters=request.filters,
        )
        return ListJobsResponse(
            items=[job.to_dict() for job in items],
            total=total,
        )
