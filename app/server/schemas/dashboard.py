"""Dashboard schemas for request/response validation."""

from pydantic import BaseModel
from typing import Any


class DashboardResponse(BaseModel):
    jobs_total: int = 0
    jobs_high_match: int = 0
    companies_total: int = 0
    skills_total: int = 0
    pending_count: int = 0
    recent_activity: list[dict[str, Any]] = []


class GenerationHistoryResponse(BaseModel):
    items: list[dict[str, Any]]


class CityListResponse(BaseModel):
    items: list[str]
