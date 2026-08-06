"""JobCompany entity — a company associated with a job posting.

A job may reference multiple companies: one hiring company plus zero or more
recruiting / staffing / agency companies. This entity captures that per-job
relationship with the extraction metadata (company_type, confidence, reason).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity

ROLE_HIRING = "hiring"
ROLE_RECRUITER = "recruiter"
VALID_ROLES = (ROLE_HIRING, ROLE_RECRUITER)


class JobCompany(BaseEntity):
    """A job ↔ company association row."""

    def __init__(
        self,
        id: int | None = None,
        job_id: str | None = None,
        company_id: str | None = None,
        role: str = ROLE_HIRING,
        company_type: str | None = None,
        confidence: float | None = None,
        reason: str | None = None,
        created_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at)
        self.job_id = job_id
        self.company_id = company_id
        self.role = role
        self.company_type = company_type
        self.confidence = confidence
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "company_id": self.company_id,
            "role": self.role,
            "company_type": self.company_type,
            "confidence": self.confidence,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
