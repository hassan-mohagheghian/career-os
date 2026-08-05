"""CompanyLink entity — external links associated with a company."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity


class CompanyLink(BaseEntity):
    """Company external link."""

    def __init__(
        self,
        id: int | None = None,
        company_id: str | None = None,
        url: str | None = None,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        extracted_content: str | None = None,
        created_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at)
        self.company_id = company_id
        self.url = url
        self.title = title
        self.description = description
        self.status = status
        self.extracted_content = extracted_content

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "extracted_content": self.extracted_content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
