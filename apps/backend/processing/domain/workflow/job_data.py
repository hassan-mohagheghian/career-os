"""JobData model — the subset of Job information used by the workflow.

The workflow loads the Job through the Jobs bounded context and maps it to
this strongly typed model so nodes never depend on raw database dicts.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class JobData(BaseModel):
    num: int | None = None
    id: str | None = None
    url: str | None = None
    company: str | None = None
    role: str | None = None
    title: str | None = None
    location: str | None = None
    description: str | None = None
    raw_description: str | None = None
    status: str | None = None
    source: str | None = None
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
    def from_job_dict(cls, data: dict[str, Any]) -> "JobData":
        return cls(
            num=data.get("num"),
            id=data.get("id"),
            url=data.get("url"),
            company=data.get("company"),
            role=data.get("role"),
            title=data.get("title"),
            location=data.get("location"),
            description=data.get("description"),
            raw_description=data.get("raw_description"),
            status=data.get("status"),
            source=data.get("source"),
            notes_raw=data.get("notes", "[]"),
            links_raw=data.get("links", "[]"),
            metadata={k: v for k, v in data.items() if k not in cls._reserved()},
        )

    @staticmethod
    def _reserved() -> set[str]:
        return {
            "num", "id", "url", "company", "role", "title", "location",
            "description", "raw_description", "status", "source", "notes", "links",
        }
