"""Company v2 list API schemas — typed DTOs for the paginated companies list."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CompanyScoresSchema(BaseModel):
    """Company intelligence score summary."""

    overall: float | None = None
    fit: float | None = None
    success: float | None = None
    overall_grade: str | None = None


class CompanyProcessingSchema(BaseModel):
    """Processing state carried on the company record."""

    status: str | None = None
    current_node: str | None = None
    progress_pct: float | None = None
    error: str | None = None


class CompanyListItemSchema(BaseModel):
    """A single company in the v2 list."""

    id: str
    name: str
    industry: str | None = None
    city: str | None = None
    country: str | None = None
    company_size: str | None = None
    company_type: str | None = None
    logo_url: str | None = None
    website: str | None = None
    description: str | None = None
    job_count: int = 0
    scores: CompanyScoresSchema | None = None
    processing: CompanyProcessingSchema | None = None
    updated_at: str | None = None
    created_at: str | None = None


class CompanyListResponseSchema(BaseModel):
    """Cursor-paginated company list response."""

    items: list[CompanyListItemSchema] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False
    total_items: int = 0


class CompanyNoteSchema(BaseModel):
    """A single company note (stored as a note: link row)."""

    id: int
    content: str
    created_at: str | None = None


class CompanyLinkItemSchema(BaseModel):
    """A single company link."""

    id: int
    url: str | None = None
    title: str | None = None
    description: str | None = None
    status: str | None = None
    created_at: str | None = None


class CompanyJobRefSchema(BaseModel):
    """A slim projection of a job linked to a company."""

    id: str
    role: str | None = None
    location: str | None = None
    match: str | None = None
    score: str | None = None
    fit_score: int | None = None
    success_score: int | None = None
    overall_score: int | None = None


class CompanyIntelligenceSchema(BaseModel):
    """Parsed company intelligence analysis."""

    overview: Any | None = None
    culture_analysis: Any | None = None
    international_analysis: Any | None = None
    career_analysis: Any | None = None
    benefits_analysis: Any | None = None
    visa_analysis: Any | None = None
    technology_analysis: Any | None = None
    recommendation: Any | None = None
    scores: dict[str, Any] | None = None
    generated_at: str | None = None


class CompanyDetailResponseSchema(BaseModel):
    """All-in-one company detail payload (mirrors the jobs v2 detail)."""

    id: str
    name: str
    website: str | None = None
    domain: str | None = None
    industry: str | None = None
    country: str | None = None
    city: str | None = None
    description: str | None = None
    company_size: str | None = None
    company_type: str | None = None
    logo_url: str | None = None
    founded_year: str | None = None
    job_count: int = 0
    status: str | None = None
    current_node: str | None = None
    progress_pct: float | None = None
    error: str | None = None
    notes: list[CompanyNoteSchema] = Field(default_factory=list)
    links: list[CompanyLinkItemSchema] = Field(default_factory=list)
    intelligence: CompanyIntelligenceSchema | None = None
    scores: CompanyScoresSchema | None = None
    jobs: list[CompanyJobRefSchema] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
