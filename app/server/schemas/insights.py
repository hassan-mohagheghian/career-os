"""Insight schemas for request/response validation."""

from pydantic import BaseModel
from typing import Any


class InsightSectionResponse(BaseModel):
    """Schema for a single insight section."""
    section: str
    data: dict[str, Any]
    updated_at: str | None = None


class InsightsResponse(BaseModel):
    """Schema for all insights response."""
    overview: dict[str, Any] | None = None
    opportunities: dict[str, Any] | None = None
    companies: dict[str, Any] | None = None
    skills: dict[str, Any] | None = None
    market: dict[str, Any] | None = None
    networking: dict[str, Any] | None = None


class InsightStatusResponse(BaseModel):
    """Schema for insight generation status."""
    sections: list[SectionStatus]


class SectionStatus(BaseModel):
    section: str
    status: str  # idle, processing, completed, failed
    last_updated: str | None = None


class InsightProgressResponse(BaseModel):
    """Schema for real-time insight progress."""
    running: bool
    status: str
    type: str | None = None
    current_section: str | None = None
    progress: dict[str, Any] | None = None


class SkillsIntelResponse(BaseModel):
    """Schema for skills intelligence response."""
    skills: list[dict[str, Any]]
    summary: dict[str, Any] | None = None
    generated_at: str | None = None


class InsightRefreshResponse(BaseModel):
    status: str = "started"
    type: str | None = None
