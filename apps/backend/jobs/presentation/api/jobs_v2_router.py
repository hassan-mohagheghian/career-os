"""New Jobs List API router — registered before legacy routes to avoid path conflicts."""

from __future__ import annotations

import json
import math
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from jobs.presentation.api.schemas.jobs_v2 import (
    JobListItemSchema,
    JobListResponseSchema,
    PaginationSchema,
    CursorPaginationSchema,
    ScoresSchema,
    ProcessingExecutionSchema,
    JobDetailResponseSchema,
    JobDetailExecutionSchema,
    JobDetailWorkflowSchema,
    JobDetailWorkflowStepSchema,
    UpdateJobRequest,
    JobNoteItem,
    JobLinkItem,
)
from jobs.application.use_cases.list_jobs_v2 import ListJobsV2UseCase, ListJobsV2Request
from jobs.infrastructure import SQLAlchemyJobRepository
from processing.infrastructure import SQLAlchemyProcessingExecutionRepository
from processing.domain.enums import ExecutionStatus
from dependencies import get_job_repo, get_processing_execution_repo

router = APIRouter()


def _parse_items(raw: Any) -> list[dict[str, Any]]:
    """Parse a stored JSON string (notes/links) into a list of items."""
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else [parsed]
        except (TypeError, ValueError):
            return []
    return []


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
            id=str(job_dict.get("id", "")),
            status=status,
            started_at=None,
            finished_at=None,
        )
    work_type = (job_dict.get("work_type") or "").lower()
    visa_raw = job_dict.get("visa")
    return JobListItemSchema(
        id=job_dict.get("id"),
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


@router.get("/list", response_model=JobListResponseSchema)
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


def _step_to_schema(step: Any) -> JobDetailWorkflowStepSchema:
    return JobDetailWorkflowStepSchema(
        id=step.get("id"),
        title=step.get("title"),
        status=step.get("status", "pending"),
        progress=step.get("progress"),
        displayable=step.get("displayable", True),
        children=[_step_to_schema(c) for c in step.get("children", [])],
        error=step.get("error"),
        started_at=step.get("started_at"),
        completed_at=step.get("completed_at"),
    )


def _workflow_to_schema(workflow: Any) -> JobDetailWorkflowSchema | None:
    if not workflow:
        return None
    current_step = workflow.get("current_step")
    return JobDetailWorkflowSchema(
        id=workflow.get("id"),
        name=workflow.get("name", "Job Context Preparation"),
        status=workflow.get("status", "pending"),
        current_step=_step_to_schema(current_step) if current_step else None,
        progress=workflow.get("progress"),
        steps=[_step_to_schema(s) for s in workflow.get("steps", [])],
    )


def _execution_to_schema(execution: Any) -> JobDetailExecutionSchema | None:
    if not execution:
        return None
    workflow = execution.workflow_progress or {}
    current_step = workflow.get("current_step") or {}
    return JobDetailExecutionSchema(
        execution_id=execution.id,
        status=execution.status.value,
        created_at=execution.created_at.isoformat() if execution.created_at else None,
        started_at=execution.started_at.isoformat() if execution.started_at else None,
        completed_at=execution.finished_at.isoformat() if execution.finished_at else None,
        error={"message": execution.error_message} if execution.error_message else None,
        current_step=current_step.get("title") or current_step.get("id"),
        workflow=_workflow_to_schema(workflow),
    )


@router.get("/{job_id}", response_model=JobDetailResponseSchema)
def get_job_detail(
    job_id: str,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    job_dict = repo.get_by_id(job_id)
    if not job_dict:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    executions = exec_repo.list_by_target("job", job_id)
    latest_execution = executions[0] if executions else None

    work_type = (job_dict.get("work_type") or "").lower()
    return JobDetailResponseSchema(
        id=job_dict.get("id"),
        title=job_dict.get("title") or job_dict.get("role"),
        company_name=job_dict.get("company"),
        role=job_dict.get("role"),
        location=job_dict.get("location"),
        work_type=job_dict.get("work_type"),
        employment_type=job_dict.get("employment_type"),
        salary=job_dict.get("salary"),
        visa=job_dict.get("visa"),
        url=job_dict.get("url"),
        status=job_dict.get("status"),
        scores=ScoresSchema(
            overall=job_dict.get("overall_score"),
            fit=job_dict.get("fit_score"),
            success=job_dict.get("success_score"),
        ),
        latest_processing_execution=_execution_to_schema(latest_execution),
        description=job_dict.get("description"),
        notes=[JobNoteItem(**x) for x in _parse_items(job_dict.get("notes"))],
        links=[JobLinkItem(**x) for x in _parse_items(job_dict.get("links"))],
        updated_at=job_dict.get("updated_at"),
        created_at=job_dict.get("created_at"),
    )


@router.delete("/{job_id}", status_code=204)
def delete_job(
    job_id: str,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    """Hard-delete a job by UUID and its related tables and executions."""
    job_dict = repo.get_by_id(job_id)
    if not job_dict:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    exec_repo.delete_by_target("job", job_id)
    if not repo.delete_by_id(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return Response(status_code=204)


@router.patch("/{job_id}", response_model=JobDetailResponseSchema)
def update_job(
    job_id: str,
    body: UpdateJobRequest,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    """Partially update a job's core data (Edit Job feature)."""
    data = body.model_dump(exclude_unset=True)
    if "notes" in data and data["notes"] is not None:
        data["notes"] = json.dumps(data["notes"], ensure_ascii=False)
    if "links" in data and data["links"] is not None:
        data["links"] = json.dumps(data["links"], ensure_ascii=False)
    job_dict = repo.update_by_id(job_id, data)
    if not job_dict:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    executions = exec_repo.list_by_target("job", job_id)
    latest_execution = executions[0] if executions else None

    return JobDetailResponseSchema(
        id=job_dict.get("id"),
        title=job_dict.get("title") or job_dict.get("role"),
        company_name=job_dict.get("company"),
        role=job_dict.get("role"),
        location=job_dict.get("location"),
        work_type=job_dict.get("work_type"),
        employment_type=job_dict.get("employment_type"),
        salary=job_dict.get("salary"),
        visa=job_dict.get("visa"),
        url=job_dict.get("url"),
        status=job_dict.get("status"),
        scores=ScoresSchema(
            overall=job_dict.get("overall_score"),
            fit=job_dict.get("fit_score"),
            success=job_dict.get("success_score"),
        ),
        latest_processing_execution=_execution_to_schema(latest_execution),
        description=job_dict.get("description"),
        notes=[JobNoteItem(**x) for x in _parse_items(job_dict.get("notes"))],
        links=[JobLinkItem(**x) for x in _parse_items(job_dict.get("links"))],
        updated_at=job_dict.get("updated_at"),
        created_at=job_dict.get("created_at"),
    )
