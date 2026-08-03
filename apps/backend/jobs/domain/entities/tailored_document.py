"""TailoredDocument entity — a resume or cover letter tailored for a specific job."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity


class TailoredDocument(BaseEntity):
    """A document (resume or cover letter) tailored for a specific job."""

    def __init__(
        self,
        id: str = "",
        title: str | None = None,
        company: str | None = None,
        role: str | None = None,
        content: str | None = None,
        version: int = 1,
        raw_text: str | None = None,
        created_at: datetime | None = None,
        job_id: str | None = None,
    ):
        super().__init__(id=id, created_at=created_at)
        self.title = title
        self.company = company
        self.role = role
        self.content = content
        self.version = version
        self.raw_text = raw_text
        self.job_id = job_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "role": self.role,
            "content": self.content,
            "version": self.version,
            "raw_text": self.raw_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "job_id": self.job_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TailoredDocument:
        return cls(
            id=data.get("id", ""),
            title=data.get("title"),
            company=data.get("company"),
            role=data.get("role"),
            content=data.get("content"),
            version=data.get("version", 1),
            raw_text=data.get("raw_text"),
            created_at=data.get("created_at"),
            job_id=data.get("job_id"),
        )
