"""New Companies List API router — paginated search/sort for the companies v2 UI.

Registered before the legacy ``companies_router`` so ``/companies/list`` is not
captured by the legacy ``/companies/{id}`` route.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, Query

from companies.infrastructure import SQLAlchemyCompanyRepository
from companies.infrastructure.repositories.sa_company_intelligence_repository import (
    SQLAlchemyCompanyIntelligenceRepository,
)
from companies.infrastructure.repositories.sa_company_link_repository import (
    SQLAlchemyCompanyLinkRepository,
)
from companies.presentation.api.schemas.companies_v2 import (
    CompanyDetailResponseSchema,
    CompanyIntelligenceSchema,
    CompanyJobRefSchema,
    CompanyLinkItemSchema,
    CompanyListResponseSchema,
    CompanyListItemSchema,
    CompanyNoteSchema,
    CompanyProcessingSchema,
    CompanyScoresSchema,
)
from dependencies import get_company_intelligence_repo, get_company_link_repo, get_company_repo, get_job_repo
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository

router = APIRouter()

DEFAULT_PAGE_SIZE = 25

SORTABLE_SCORE_FIELDS = ("overall_score", "fit_score", "success_score")

SCORE_KEY_MAP = {
    "overall_score": "company_overall_score",
    "fit_score": "company_fit_score",
    "success_score": "company_success_score",
}


def _cursor_decode(cursor: str) -> int:
    """Decode an opaque base64 offset cursor; invalid cursors restart at 0."""
    if not cursor:
        return 0
    try:
        return int(base64.b64decode(cursor.encode()).decode())
    except Exception:
        return 0


def _cursor_encode(offset: int) -> str:
    return base64.b64encode(str(offset).encode()).decode()


def _matches(row: dict[str, Any], query: str, industry: str) -> bool:
    if query:
        q = query.lower()
        haystacks = [
            row.get("name"),
            row.get("industry"),
            row.get("city"),
            row.get("country"),
            row.get("description"),
        ]
        if not any(h and q in str(h).lower() for h in haystacks):
            return False
    if industry:
        if (row.get("industry") or "") != industry:
            return False
    return True


def _score_value(row: dict[str, Any], sort: str) -> Any:
    scores = row.get("_scores") or {}
    return scores.get(SCORE_KEY_MAP[sort])


def _sort_key(row: dict[str, Any], sort: str) -> Any:
    if sort in SORTABLE_SCORE_FIELDS:
        return _score_value(row, sort)
    if sort == "name":
        return (row.get("name") or "").lower()
    if sort == "updated_at":
        return row.get("updated_at")
    return row.get("created_at")


def _to_list_item(row: dict[str, Any]) -> CompanyListItemSchema:
    scores = row.get("_scores") or {}
    return CompanyListItemSchema(
        id=row["id"],
        name=row.get("name") or "",
        industry=row.get("industry"),
        city=row.get("city"),
        country=row.get("country"),
        company_size=row.get("company_size"),
        company_type=row.get("company_type"),
        logo_url=row.get("logo_url"),
        website=row.get("website"),
        description=row.get("description"),
        job_count=row.get("job_count", 0),
        scores=CompanyScoresSchema(
            overall=scores.get("company_overall_score"),
            fit=scores.get("company_fit_score"),
            success=scores.get("company_success_score"),
            overall_grade=scores.get("overall_grade") or scores.get("fit_grade"),
        ),
        processing=CompanyProcessingSchema(
            status=row.get("status"),
            current_node=row.get("current_node"),
            progress_pct=row.get("progress_pct"),
            error=row.get("error"),
        ),
        updated_at=row.get("updated_at"),
        created_at=row.get("created_at"),
    )


@router.get("/list")
def list_companies_v2(
    query: str = Query("", description="Substring search over name, industry, city, country, description"),
    industry: str = Query("", description="Exact industry filter"),
    sort: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="asc or desc"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=200),
    cursor: str = Query("", description="Opaque pagination cursor"),
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
) -> CompanyListResponseSchema:
    """List companies with server-side search, filter, sort and cursor pagination."""
    rows = [r for r in repo.list_all_with_details() if _matches(r, query, industry)]

    key: Callable[[dict[str, Any]], Any] = lambda r: _sort_key(r, sort)
    with_value = [r for r in rows if key(r) is not None]
    without_value = [r for r in rows if key(r) is None]
    with_value.sort(key=key, reverse=(order == "desc"))
    rows = with_value + without_value

    total = len(rows)
    offset = _cursor_decode(cursor)
    page = rows[offset:offset + page_size]
    next_offset = offset + len(page)
    has_more = next_offset < total

    return CompanyListResponseSchema(
        items=[_to_list_item(r) for r in page],
        next_cursor=_cursor_encode(next_offset) if has_more else None,
        has_more=has_more,
        total_items=total,
    )


def _parse_json_field(value: Any) -> Any:
    """Best-effort JSON parse of a stored Text column value."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def _scores_from_intelligence(intel: dict[str, Any] | None) -> CompanyScoresSchema | None:
    if not intel:
        return None
    scores = _parse_json_field(intel.get("scores")) or {}
    if not isinstance(scores, dict):
        scores = {}
    return CompanyScoresSchema(
        overall=scores.get("company_overall_score"),
        fit=scores.get("company_fit_score"),
        success=scores.get("company_success_score"),
        overall_grade=scores.get("overall_grade") or scores.get("fit_grade"),
    )


def _to_intelligence_schema(intel: dict[str, Any] | None) -> CompanyIntelligenceSchema | None:
    if not intel:
        return None
    return CompanyIntelligenceSchema(
        overview=_parse_json_field(intel.get("overview")),
        culture_analysis=_parse_json_field(intel.get("culture_analysis")),
        international_analysis=_parse_json_field(intel.get("international_analysis")),
        career_analysis=_parse_json_field(intel.get("career_analysis")),
        benefits_analysis=_parse_json_field(intel.get("benefits_analysis")),
        visa_analysis=_parse_json_field(intel.get("visa_analysis")),
        technology_analysis=_parse_json_field(intel.get("technology_analysis")),
        recommendation=_parse_json_field(intel.get("recommendation")),
        scores=_parse_json_field(intel.get("scores")) or None,
        generated_at=intel.get("generated_at"),
    )


@router.get("/{id}", response_model=CompanyDetailResponseSchema)
def get_company_detail(
    id: str,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
    intel_repo: SQLAlchemyCompanyIntelligenceRepository = Depends(get_company_intelligence_repo),
    link_repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo),
    job_repo: SQLAlchemyJobRepository = Depends(get_job_repo),
) -> CompanyDetailResponseSchema:
    """Get a company by id with all related data in a single payload."""
    company = repo.get_by_id(id)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {id} not found")

    intel = intel_repo.get_by_company_id(id)
    links = link_repo.get_by_company_id(id)
    jobs = job_repo.get_jobs_by_company_id(id)

    notes = [
        CompanyNoteSchema(id=l["id"], content=l.get("title", "").removeprefix("note:"), created_at=l.get("created_at"))
        for l in links
        if l.get("title", "").startswith("note:")
    ]
    links_schema = [
        CompanyLinkItemSchema(
            id=l["id"],
            url=l.get("url"),
            title=l.get("title"),
            description=l.get("description"),
            status=l.get("status"),
            created_at=l.get("created_at"),
        )
        for l in links
        if not l.get("title", "").startswith("note:")
    ]
    jobs_schema = [
        CompanyJobRefSchema(
            id=j["id"],
            role=j.get("role"),
            location=j.get("location"),
            match=j.get("match"),
            score=j.get("score"),
            fit_score=j.get("fit_score"),
            success_score=j.get("success_score"),
            overall_score=j.get("overall_score"),
        )
        for j in jobs
    ]

    return CompanyDetailResponseSchema(
        id=company["id"],
        name=company.get("name") or "",
        website=company.get("website"),
        domain=company.get("domain"),
        industry=company.get("industry"),
        country=company.get("country"),
        city=company.get("city"),
        description=company.get("description"),
        company_size=company.get("company_size"),
        company_type=company.get("company_type"),
        logo_url=company.get("logo_url"),
        founded_year=company.get("founded_year"),
        job_count=len(jobs_schema),
        status=company.get("status"),
        current_node=company.get("current_node"),
        progress_pct=company.get("progress_pct"),
        error=company.get("error"),
        notes=notes,
        links=links_schema,
        intelligence=_to_intelligence_schema(intel),
        scores=_scores_from_intelligence(intel),
        jobs=jobs_schema,
        created_at=company.get("created_at"),
        updated_at=company.get("updated_at"),
    )
