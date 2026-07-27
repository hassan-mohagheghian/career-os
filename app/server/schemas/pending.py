"""Pending job schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Any


class PendingCreate(BaseModel):
    """Schema for queueing a new job."""
    url: str = Field(..., min_length=1)
    notes: str | None = None
    links: list[str] = []
    company: str | None = None


class PendingResponse(BaseModel):
    """Schema for pending job response."""
    id: str
    url: str
    status: str
    source: str | None = None
    company: str | None = None
    error: str | None = None
    job_num: int | None = None
    version: int = 1
    step_fetch: int = 0
    step_validate: int = 0
    step_extract_raw: int = 0
    step_extract_struct: int = 0
    step_analyze: int = 0
    step_summary: int = 0
    step_db: int = 0
    step_done: int = 0
    workflow_log: list[Any] = []
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class PendingListResponse(BaseModel):
    items: list[PendingResponse]
    total: int


class QueueAllResponse(BaseModel):
    queued: int
