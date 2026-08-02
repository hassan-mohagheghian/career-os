"""ListJobsV2 use case — new jobs list for the row-based UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jobs.domain.repositories.job_repository import IJobRepository


@dataclass
class ListJobsV2Request:
    page: int = 1
    page_size: int = 25
    cursor: str | None = None
    query: str | None = None
    sort: str = "updated_at"
    order: str = "desc"
    processing_status: str | None = None
    company_id: int | None = None
    remote: bool | None = None
    visa: bool | None = None
    overall_score_min: int | None = None
    overall_score_max: int | None = None
    fit_score_min: int | None = None
    fit_score_max: int | None = None
    success_score_min: int | None = None
    success_score_max: int | None = None


@dataclass
class ListJobsV2Response:
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    next_cursor: str | None = None
    has_more: bool = False


class ListJobsV2UseCase:
    def __init__(self, job_repository: IJobRepository):
        self._job_repository = job_repository

    def execute(self, request: ListJobsV2Request) -> ListJobsV2Response:
        items, total, next_cursor, has_more = self._job_repository.search_jobs_cursor(
            cursor=request.cursor,
            page_size=request.page_size,
            page=request.page,
            query=request.query,
            sort=request.sort,
            order=request.order,
            processing_status=request.processing_status,
            company_id=request.company_id,
            remote=request.remote,
            visa=request.visa,
            overall_score_min=request.overall_score_min,
            overall_score_max=request.overall_score_max,
            fit_score_min=request.fit_score_min,
            fit_score_max=request.fit_score_max,
            success_score_min=request.success_score_min,
            success_score_max=request.success_score_max,
        )
        return ListJobsV2Response(
            items=items,
            total=total,
            page=request.page if request.cursor is None else 1,
            page_size=request.page_size,
            next_cursor=next_cursor,
            has_more=has_more,
        )
