"""CompanyService — application service for loading and persisting Company data.

The Companies bounded context owns Company loading and persistence. The
processing workflow depends on this service (via the Company repository and the
Company intelligence repository) rather than accessing the database directly
from workflow nodes.
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from typing import Any

from companies.domain.repositories.company_intelligence_repository import ICompanyIntelligenceRepository
from companies.domain.repositories.company_link_repository import ICompanyLinkRepository
from companies.domain.repositories.company_repository import ICompanyRepository
from shared.application.exceptions import NotFoundError


class CompanyService:
    def __init__(
        self,
        repository: ICompanyRepository,
        intelligence_repository: ICompanyIntelligenceRepository,
        link_repository: ICompanyLinkRepository | None = None,
    ):
        self._repository = repository
        self._intelligence = intelligence_repository
        self._links = link_repository

    def get_company(self, company_id: str) -> dict[str, Any] | None:
        """Load a company by its UUID.

        When a link repository is available the returned dict also carries
        ``notes`` (text notes) and ``links`` (URL links) sourced from the
        ``company_links`` table, so the context preparation phase can collect
        them as sources.
        """
        company = self._repository.get_by_id(company_id)
        if company is None or self._links is None:
            return company

        link_rows = self._links.get_by_company_id(company_id)
        notes = [
            {"type": "text", "content": row.get("title", "").removeprefix("note:").strip()}
            for row in link_rows
            if row.get("title", "").startswith("note:")
        ]
        links = [
            {"url": row.get("url"), "title": row.get("title") or ""}
            for row in link_rows
            if not row.get("title", "").startswith("note:")
        ]
        merged = dict(company)
        merged["notes"] = json.dumps(notes, ensure_ascii=False)
        merged["links"] = json.dumps(links, ensure_ascii=False)
        return merged

    def get_company_or_raise(self, company_id: str) -> dict[str, Any]:
        company = self.get_company(company_id)
        if not company:
            raise NotFoundError(f"Company {company_id} not found")
        return company

    def persist_prepared_context(self, company_id: str, combined_text: str) -> None:
        """Persist the prepared context so it survives the in-memory pipeline.

        The analysis phase reads this text as its durable LLM input. Stored on
        the company as raw_content (the raw fetched/extracted text).
        """
        self._repository.update_fields(
            company_id,
            raw_content=combined_text,
        )

    def persist_analysis(
        self,
        company_id: str,
        extraction: dict[str, Any],
        intelligence: dict[str, Any],
        recommendation: dict[str, Any],
        scores: dict[str, Any],
        raw_source: str = "",
    ) -> None:
        """Persist a completed company analysis.

        Writes the queryable extraction fields onto the companies row, upserts
        the company_intelligence row (sections + recommendation + scores), and
        marks the company as processed.
        """
        now = datetime.now(UTC).isoformat()

        fields: dict[str, Any] = {
            "name": extraction.get("name", ""),
            "website": extraction.get("website", ""),
            "domain": extraction.get("domain", ""),
            "industry": extraction.get("industry", ""),
            "country": extraction.get("country", ""),
            "city": extraction.get("city", ""),
            "description": extraction.get("description", ""),
            "company_size": extraction.get("company_size", ""),
            "company_type": extraction.get("company_type", ""),
            "logo_url": extraction.get("logo_url", ""),
            "founded_year": extraction.get("founded_year", ""),
            "headquarters_full": extraction.get("headquarters_full", ""),
            "countries_of_operation": json.dumps(extraction.get("countries_of_operation", []), ensure_ascii=False),
            "products": json.dumps(extraction.get("products", []), ensure_ascii=False),
            "tech_stack": json.dumps(extraction.get("tech_stack", {}), ensure_ascii=False),
            "work_environment": json.dumps(extraction.get("work_environment", {}), ensure_ascii=False),
            "funding_stage": extraction.get("funding_stage", ""),
            "funding_amount": extraction.get("funding_amount", ""),
            "status": "processed",
            "updated_at": now,
        }
        self._repository.update_fields(company_id, **fields)

        intel_data = {
            "overview": json.dumps(intelligence.get("overview", {}), ensure_ascii=False),
            "culture_analysis": json.dumps(intelligence.get("culture_analysis", {}), ensure_ascii=False),
            "international_analysis": json.dumps(intelligence.get("international_analysis", {}), ensure_ascii=False),
            "career_analysis": json.dumps(intelligence.get("career_analysis", {}), ensure_ascii=False),
            "benefits_analysis": json.dumps(intelligence.get("benefits_analysis", {}), ensure_ascii=False),
            "visa_analysis": json.dumps(intelligence.get("visa_analysis", {}), ensure_ascii=False),
            "technology_analysis": json.dumps(intelligence.get("technology_analysis", {}), ensure_ascii=False),
            "recommendation": json.dumps(recommendation, ensure_ascii=False),
            "scores": json.dumps(scores, ensure_ascii=False),
            "raw_source_data": json.dumps(raw_source[:10000] if raw_source else "", ensure_ascii=False),
            "generated_at": now,
        }
        self._intelligence.upsert(company_id, intel_data)

    def create_from_intake(
        self,
        name: str = "",
        notes: list[dict[str, Any]] | None = None,
        links: list[dict[str, Any]] | list[str] | None = None,
        source: str = "web",
        input_type: str = "url",
    ) -> dict[str, Any]:
        """Create a company row from intake (notes + links) and return it.

        Text notes are stored as ``note:`` link rows and URL links as URL link
        rows in the ``company_links`` table — the canonical, separate storage
        for a company's notes and links. The context preparation phase collects
        them as sources through ``get_company``.
        """
        company = self._repository.insert({
            "name": name or "",
            "source": source,
            "input_type": input_type,
            "status": "created",
        })
        if self._links is not None:
            for note in notes or []:
                content = note.get("content", "") if isinstance(note, dict) else str(note)
                if content:
                    self._links.create(company["id"], "", f"note:{content}")
            for link in links or []:
                url = link.get("url", "") if isinstance(link, dict) else str(link)
                title = link.get("title", "") if isinstance(link, dict) else ""
                if url:
                    self._links.create(company["id"], url, title)
        return company

    def update_status(self, company_id: str, status: str, **extra: Any) -> bool:
        """Update the company model status (JobStatus vocabulary)."""
        return self._repository.update_status(company_id, status, **extra)
