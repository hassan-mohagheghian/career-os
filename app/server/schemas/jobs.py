"""Job schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Any


class JobCreate(BaseModel):
    """Schema for creating a new job."""
    url: str = Field(..., description="Job posting URL")
    notes: str | None = Field(None, description="Additional notes")
    links: list[str] = Field(default_factory=list, description="Related links")


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    apply_time: str | None = None
    response_time: str | None = None
    response_status: str | None = None
    notes: str | None = None


class JobResponse(BaseModel):
    """Schema for job response."""
    num: int
    url: str
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None
    notes: str | None = None
    fit_score: float | None = None
    success_score: float | None = None
    overall_score: float | None = None
    score: str | None = None
    match: str | None = None
    work_type: str | None = None
    employment_type: str | None = None
    status: str | None = None
    deleted: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    linked_company: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Schema for paginated job list."""
    jobs: list[JobResponse]
    total: int
    agg: dict[str, int] | None = None


class JobRequeueResponse(BaseModel):
    status: str = "queued"
    pid: int
    num: int
    company: str | None = None


class JobRescoreResponse(BaseModel):
    status: str = "queued"
    num: int
    company: str | None = None
    pending_id: int


class JobDeleteResponse(BaseModel):
    status: str = "deleted"
    num: int


class RescoreAllResponse(BaseModel):
    status: str = "rescoring"
    count: int


class ReprocessAllResponse(BaseModel):
    status: str = "reprocessing"
    count: int
