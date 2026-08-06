"""CompanyData model — the subset of Company information used by the workflow.

The workflow loads the Company through the Companies bounded context and maps
it to this strongly typed model so nodes never depend on raw database dicts.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CompanyData(BaseModel):
    id: str | None = None
    name: str | None = None
    website: str | None = None
    domain: str | None = None
    industry: str | None = None
    city: str | None = None
    country: str | None = None
    description: str | None = None
    raw_content: str | None = None
    status: str | None = None
    source: str | None = None
    company_type: str | None = None
    notes_raw: str = "[]"
    links_raw: str = "[]"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("notes_raw", "links_raw", mode="before")
    @classmethod
    def _raw_can_be_none(cls, v: Any) -> str:
        if v is None:
            return "[]"
        if not isinstance(v, str):
            return str(v)
        return v

    @classmethod
    def from_company_dict(cls, data: dict[str, Any]) -> "CompanyData":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            website=data.get("website"),
            domain=data.get("domain"),
            industry=data.get("industry"),
            city=data.get("city"),
            country=data.get("country"),
            description=data.get("description"),
            raw_content=data.get("raw_content"),
            status=data.get("status"),
            source=data.get("source"),
            company_type=data.get("company_type"),
            notes_raw=data.get("notes", "[]"),
            links_raw=data.get("links", "[]"),
            metadata={k: v for k, v in data.items() if k not in cls._reserved()},
        )

    @staticmethod
    def _reserved() -> set[str]:
        return {
            "id", "name", "website", "domain", "industry", "city", "country",
            "description", "raw_content", "status", "source", "company_type",
            "notes", "links",
        }
