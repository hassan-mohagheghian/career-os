"""New Jobs List API schemas — JobListItem DTO matching docs/domain/jobs/job-list-item.md."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ScoresSchema(BaseModel):
    overall: int | None = None
    fit: int | None = None
    success: int | None = None


class ProcessingExecutionSchema(BaseModel):
    id: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None


class JobListItemSchema(BaseModel):
    id: str
    num: int
    title: str | None = None
    company_name: str | None = Field(default=None, validation_alias="company")
    location: str | None = None
    remote: bool | None = None
    visa_sponsorship: bool | None = None
    job_status: str | None = Field(default=None, validation_alias="status")
    latest_processing_execution: ProcessingExecutionSchema | None = None
    scores: ScoresSchema | None = None
    updated_at: str | None = None
    created_at: str | None = None

    model_config = {"populate_by_name": True, "from_attributes": True}


class PaginationSchema(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class CursorPaginationSchema(BaseModel):
    total_items: int
    next_cursor: str | None = None
    has_more: bool = False


class JobListResponseSchema(BaseModel):
    items: list[JobListItemSchema] = Field(default_factory=list)
    pagination: PaginationSchema | None = None
    cursor_pagination: CursorPaginationSchema | None = None


class JobDetailWorkflowStepSchema(BaseModel):
    id: str
    title: str
    status: str = "pending"
    progress: float | None = None
    displayable: bool = True
    children: list["JobDetailWorkflowStepSchema"] = Field(default_factory=list)
    error: dict[str, str] | None = None
    started_at: str | None = None
    completed_at: str | None = None


class JobDetailWorkflowSchema(BaseModel):
    id: str
    name: str = "Job Context Preparation"
    status: str = "pending"
    current_step: JobDetailWorkflowStepSchema | None = None
    progress: float | None = None
    steps: list[JobDetailWorkflowStepSchema] = Field(default_factory=list)


class JobDetailExecutionSchema(BaseModel):
    execution_id: str
    status: str
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    error: dict[str, str] | None = None
    current_step: str | None = None
    workflow: JobDetailWorkflowSchema | None = None


class JobDetailResponseSchema(BaseModel):
    id: str
    num: int
    title: str | None = None
    company_name: str | None = Field(default=None, validation_alias="company")
    role: str | None = None
    location: str | None = None
    work_type: str | None = None
    employment_type: str | None = None
    salary: str | None = None
    visa: str | None = None
    url: str | None = None
    status: str | None = None
    scores: ScoresSchema | None = None
    latest_processing_execution: JobDetailExecutionSchema | None = None
    description: str | None = None
    notes: str | None = None
    updated_at: str | None = None
    created_at: str | None = None

    model_config = {"populate_by_name": True, "from_attributes": True}
