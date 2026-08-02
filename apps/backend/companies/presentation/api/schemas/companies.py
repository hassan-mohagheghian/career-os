"""Company schemas for request/response validation."""

from pydantic import BaseModel
from typing import Any


class CompanyCreate(BaseModel):
    """Schema for creating a new company."""
    name: str
    industry: str | None = None
    city: str | None = None
    country: str | None = None
    logo_url: str | None = None
    notes: str | None = None


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""
    name: str | None = None
    industry: str | None = None
    city: str | None = None
    country: str | None = None
    logo_url: str | None = None
    notes: str | None = None


class CompanyResponse(BaseModel):
    """Schema for company response."""
    id: int
    name: str
    industry: str | None = None
    city: str | None = None
    country: str | None = None
    logo_url: str | None = None
    notes: str | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    items: list[CompanyResponse]
    total: int


class CompanyIntelligenceResponse(BaseModel):
    company_id: int
    overview: str | None = None
    culture: str | None = None
    tech_stack: list[str] = []
    visa_policy: str | None = None
    last_updated: str | None = None


class NoteCreate(BaseModel):
    content: str


class NoteResponse(BaseModel):
    id: int
    company_id: int
    content: str
    created_at: str | None = None


class LinkCreate(BaseModel):
    url: str
    label: str | None = None


class LinkResponse(BaseModel):
    id: int
    company_id: int
    url: str
    label: str | None = None
    created_at: str | None = None


class PendingCompanyCreate(BaseModel):
    name: str
    notes: str | None = None
    links: list[str] = []


class PendingCompanyResponse(BaseModel):
    id: str
    name: str
    status: str
    notes: str | None = None
    error: str | None = None
    created_at: str | None = None
