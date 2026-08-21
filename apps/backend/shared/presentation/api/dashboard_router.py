"""Dashboard data, generation history."""

from fastapi import APIRouter, Depends, Query

from dependencies import get_job_repo, get_company_repo, get_skill_repo, get_session_sync
from jobs.infrastructure import SQLAlchemyJobRepository
from companies.infrastructure import SQLAlchemyCompanyRepository
from skills.infrastructure import SQLAlchemySkillRepository

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(
    job_repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
    skill_repo: SQLAlchemySkillRepository = Depends(get_skill_repo),
):
    """Get dashboard summary data."""
    job_counts = job_repo.get_dashboard_counts()
    companies_total = company_repo.get_total_count()
    skills_total = len([s for s in skill_repo.list_visible() if not s.get("hidden")])

    return {
        "jobs_total": job_counts["jobs_total"],
        "jobs_high_match": job_counts["jobs_high_match"],
        "companies_total": companies_total,
        "skills_total": skills_total,
        "recent_activity": [],
    }


@router.get("/generation-history")
def get_generation_history(limit: int = 50, offset: int = 0):
    """Get unified generation history from ALL source tables."""
    from shared.infrastructure.repositories.generation_repository import GenerationHistoryRepository
    from dependencies import get_session_sync

    session = get_session_sync()
    try:
        repo = GenerationHistoryRepository(session)
        result = repo.get_all(limit=limit, offset=offset)
        return {
            "items": [item.to_dict() for item in result['items']],
            "total": result['total'],
            "offset": offset,
            "limit": limit,
        }
    finally:
        session.close()


@router.get("/local-history")
def get_local_history(
    context: str = Query(..., description="Context: job, company"),
    job_id: str | None = Query(None),
    company_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Get local generation history filtered by context."""
    from shared.infrastructure.repositories.generation_repository import GenerationHistoryRepository

    session = get_session_sync()
    try:
        repo = GenerationHistoryRepository(session)
        if context == 'job' and job_id is not None:
            result = repo.get_for_job(job_id, limit)
        elif context == 'company' and company_id is not None:
            result = repo.get_for_company(company_id, limit)
        else:
            result = {'items': [], 'total': 0}

        return {
            'items': [item.to_dict() for item in result['items']],
            'total': result['total'],
        }
    finally:
        session.close()


@router.get("/local-history/active")
def get_local_active_count(
    context: str = Query(...),
    job_id: str | None = Query(None),
    company_id: str | None = Query(None),
):
    """Get count of currently running/queued items for a context."""
    from shared.infrastructure.repositories.generation_repository import GenerationHistoryRepository

    session = get_session_sync()
    try:
        repo = GenerationHistoryRepository(session)
        count = repo.get_active_count(
            context,
            job_id=job_id,
            company_id=company_id,
        )
        return {'active_count': count}
    finally:
        session.close()
