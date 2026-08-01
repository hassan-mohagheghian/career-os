"""New Jobs List API router — registered before legacy routes to avoid path conflicts."""

from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter, Depends, Query

from jobs.presentation.api.schemas.jobs_v2 import (
    JobListItemSchema,
    JobListResponseSchema,
    PaginationSchema,
    CursorPaginationSchema,
    ScoresSchema,
    ProcessingExecutionSchema,
)
from jobs.application.use_cases.list_jobs_v2 import ListJobsV2UseCase, ListJobsV2Request
from jobs.infrastructure import SQLAlchemyJobRepository
from dependencies import get_job_repo

router = APIRouter()


def _v2_job_to_schema(job_dict: dict[str, Any]) -> JobListItemSchema:
    scores = ScoresSchema(
        overall=job_dict.get("overall_score"),
        fit=job_dict.get("fit_score"),
        success=job_dict.get("success_score"),
    )
    status = job_dict.get("status", "imported")
    exec_schema = None
    if status in ("queued", "processing", "running", "completed", "failed", "cancelled"):
        exec_schema = ProcessingExecutionSchema(
            id=str(job_dict.get("num", "")),
            status=status,
            started_at=None,
            finished_at=None,
        )
    work_type = (job_dict.get("work_type") or "").lower()
    visa_raw = job_dict.get("visa")
    return JobListItemSchema(
        id=job_dict.get("id"),
        num=job_dict.get("num"),
        title=job_dict.get("title") or job_dict.get("role"),
        company_name=job_dict.get("company"),
        location=job_dict.get("location"),
        remote=work_type == "remote",
        visa_sponsorship=bool(visa_raw and str(visa_raw).strip()),
        job_status=status,
        latest_processing_execution=exec_schema,
        scores=scores,
        updated_at=job_dict.get("updated_at"),
        created_at=job_dict.get("created_at"),
    )


@router.get("", response_model=JobListResponseSchema)
def list_jobs_v2(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None),
    query: str | None = Query(None),
    sort: str = Query("updated_at"),
    order: str = Query("desc"),
    processing_status: str | None = Query(None),
    company_id: int | None = Query(None),
    remote: bool | None = Query(None),
    visa: bool | None = Query(None),
    overall_score_min: int | None = Query(None),
    overall_score_max: int | None = Query(None),
    fit_score_min: int | None = Query(None),
    fit_score_max: int | None = Query(None),
    success_score_min: int | None = Query(None),
    success_score_max: int | None = Query(None),
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
):
    request = ListJobsV2Request(
        page=page, page_size=page_size, cursor=cursor, query=query, sort=sort, order=order,
        processing_status=processing_status, company_id=company_id,
        remote=remote, visa=visa,
        overall_score_min=overall_score_min, overall_score_max=overall_score_max,
        fit_score_min=fit_score_min, fit_score_max=fit_score_max,
        success_score_min=success_score_min, success_score_max=success_score_max,
    )
    use_case = ListJobsV2UseCase(repo)
    result = use_case.execute(request)
    items = [_v2_job_to_schema(j) for j in result.items]
    total_pages = max(1, math.ceil(result.total / page_size)) if result.total else 1
    return JobListResponseSchema(
        items=items,
        pagination=PaginationSchema(
            page=page, page_size=page_size,
            total_items=result.total, total_pages=total_pages,
        ),
        cursor_pagination=CursorPaginationSchema(
            total_items=result.total,
            next_cursor=result.next_cursor,
            has_more=result.has_more,
        ),
    )
