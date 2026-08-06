"""Company entity — aggregate root for the Companies bounded context."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity


class Company(BaseEntity):
    """Company aggregate root."""

    def __init__(
        self,
        id: int | None = None,
        name: str | None = None,
        website: str | None = None,
        domain: str | None = None,
        industry: str | None = None,
        country: str | None = None,
        city: str | None = None,
        description: str | None = None,
        company_size: str | None = None,
        company_type: str | None = None,
        logo_url: str | None = None,
        founded_year: str | None = None,
        headquarters_full: str | None = None,
        countries_of_operation: str | None = None,
        funding_stage: str | None = None,
        funding_amount: str | None = None,
        products: str | None = None,
        tech_stack: str | None = None,
        work_environment: str | None = None,
        extra: str | None = None,
        status: str = "pending",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        queue_order: int = 0,
        current_node: str | None = None,
        progress_pct: float = 0,
        error: str | None = None,
        retry_count: int = 0,
        failure_reason: str | None = None,
        failure_step: str | None = None,
        failure_timestamp: str | None = None,
        session_id: str | None = None,
        parent_company_id: str | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.name = name
        self.website = website
        self.domain = domain
        self.industry = industry
        self.country = country
        self.city = city
        self.description = description
        self.company_size = company_size
        self.company_type = company_type
        self.logo_url = logo_url
        self.founded_year = founded_year
        self.headquarters_full = headquarters_full
        self.countries_of_operation = countries_of_operation
        self.funding_stage = funding_stage
        self.funding_amount = funding_amount
        self.products = products
        self.tech_stack = tech_stack
        self.work_environment = work_environment
        self.extra = extra
        self.status = status
        self.queue_order = queue_order
        self.current_node = current_node
        self.progress_pct = progress_pct
        self.error = error
        self.retry_count = retry_count
        self.failure_reason = failure_reason
        self.failure_step = failure_step
        self.failure_timestamp = failure_timestamp
        self.session_id = session_id
        self.parent_company_id = parent_company_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "website": self.website,
            "domain": self.domain,
            "industry": self.industry,
            "country": self.country,
            "city": self.city,
            "description": self.description,
            "company_size": self.company_size,
            "company_type": self.company_type,
            "logo_url": self.logo_url,
            "founded_year": self.founded_year,
            "headquarters_full": self.headquarters_full,
            "countries_of_operation": self.countries_of_operation,
            "funding_stage": self.funding_stage,
            "funding_amount": self.funding_amount,
            "products": self.products,
            "tech_stack": self.tech_stack,
            "work_environment": self.work_environment,
            "extra": self.extra,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "queue_order": self.queue_order,
            "current_node": self.current_node,
            "progress_pct": self.progress_pct,
            "error": self.error,
            "retry_count": self.retry_count,
            "failure_reason": self.failure_reason,
            "failure_step": self.failure_step,
            "failure_timestamp": self.failure_timestamp,
            "session_id": self.session_id,
            "parent_company_id": self.parent_company_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Company:
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            website=data.get("website"),
            domain=data.get("domain"),
            industry=data.get("industry"),
            country=data.get("country"),
            city=data.get("city"),
            description=data.get("description"),
            company_size=data.get("company_size"),
            company_type=data.get("company_type"),
            logo_url=data.get("logo_url"),
            founded_year=data.get("founded_year"),
            headquarters_full=data.get("headquarters_full"),
            countries_of_operation=data.get("countries_of_operation"),
            funding_stage=data.get("funding_stage"),
            funding_amount=data.get("funding_amount"),
            products=data.get("products"),
            tech_stack=data.get("tech_stack"),
            work_environment=data.get("work_environment"),
            extra=data.get("extra"),
            status=data.get("status", "pending"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            queue_order=data.get("queue_order", 0),
            current_node=data.get("current_node"),
            progress_pct=data.get("progress_pct", 0),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            failure_reason=data.get("failure_reason"),
            failure_step=data.get("failure_step"),
            failure_timestamp=data.get("failure_timestamp"),
            session_id=data.get("session_id"),
            parent_company_id=data.get("parent_company_id"),
        )
