"""Dashboard data, generation history, cities."""

import json

from fastapi import APIRouter, Depends, Query

from dependencies import get_job_repo, get_company_repo, get_skill_repo, get_pending_repo
from jobs.infrastructure import SQLAlchemyJobRepository
from companies.infrastructure import SQLAlchemyCompanyRepository
from skills.infrastructure import SQLAlchemySkillRepository
from processing.infrastructure import SQLAlchemyPendingRepository

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(
    job_repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
    skill_repo: SQLAlchemySkillRepository = Depends(get_skill_repo),
    pending_repo: SQLAlchemyPendingRepository = Depends(get_pending_repo),
):
    """Get dashboard summary data."""
    job_counts = job_repo.get_dashboard_counts()
    companies_total = company_repo.get_total_count()
    skills_total = len([s for s in skill_repo.list_visible() if not s.get("hidden")])
    pending_count = pending_repo.count_pending("pending_jobs")

    return {
        "jobs_total": job_counts["jobs_total"],
        "jobs_high_match": job_counts["jobs_high_match"],
        "companies_total": companies_total,
        "skills_total": skills_total,
        "pending_count": pending_count,
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
    context: str = Query(..., description="Context: job, company, skill, insight"),
    job_num: int | None = Query(None),
    company_id: int | None = Query(None),
    skill_name: str | None = Query(None),
    insight_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Get local generation history filtered by context."""
    from shared.infrastructure.repositories.generation_repository import GenerationHistoryRepository
    from dependencies import get_session_sync

    session = get_session_sync()
    try:
        repo = GenerationHistoryRepository(session)
        if context == 'job' and job_num is not None:
            result = repo.get_for_job(job_num, limit)
        elif context == 'company' and company_id is not None:
            result = repo.get_for_company(company_id, limit)
        elif context == 'skill' and skill_name is not None:
            result = repo.get_for_skill(skill_name, limit)
        elif context == 'insight' and insight_type is not None:
            result = repo.get_for_insight(insight_type, limit)
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
    job_num: int | None = Query(None),
    company_id: int | None = Query(None),
    skill_name: str | None = Query(None),
    insight_type: str | None = Query(None),
):
    """Get count of currently running/queued items for a context."""
    from shared.infrastructure.repositories.generation_repository import GenerationHistoryRepository
    from dependencies import get_session_sync

    session = get_session_sync()
    try:
        repo = GenerationHistoryRepository(session)
        count = repo.get_active_count(
            context,
            job_num=job_num,
            company_id=company_id,
            skill_name=skill_name,
            insight_type=insight_type,
        )
        return {'active_count': count}
    finally:
        session.close()


@router.get("/cities")
def get_cities(job_repo: SQLAlchemyJobRepository = Depends(get_job_repo)):
    """Get all unique cities with job counts."""
    location_data = job_repo.get_location_data()

    city_counts = {}
    for row in location_data:
        locations = []
        if row.get("locations"):
            try:
                locations = (
                    json.loads(row["locations"])
                    if isinstance(row["locations"], str)
                    else row["locations"]
                )
            except (json.JSONDecodeError, TypeError):
                pass
        if not locations and row.get("location"):
            locations = [row["location"]]
        for loc in locations:
            if loc and loc != "Not specified":
                city_counts[loc] = city_counts.get(loc, 0) + 1

    city_info = {
        "Berlin": {"icon": "🐻", "info": "Largest tech hub. 350K+ tech workers."},
        "Munich": {"icon": "🦁", "info": "Highest salaries. Enterprise & automotive."},
        "Hamburg": {"icon": "🎵", "info": "Growing tech scene. AdTech, energy."},
        "Heidelberg": {"icon": "🏛️", "info": "Enterprise AI startup scene."},
        "Frankfurt": {"icon": "🏦", "info": "FinTech capital. Banking infrastructure."},
        "Cologne": {"icon": "🗼", "info": "Media & commerce tech."},
        "Stuttgart": {"icon": "🏭", "info": "Engineering & automotive."},
        "Remote": {"icon": "🏠", "info": "Best for visa from Iran."},
        "Remote Germany": {"icon": "🏠", "info": "Best for visa from Iran."},
        "Germany": {"icon": "🇩🇪", "info": "Country-wide opportunities."},
    }

    total_jobs = len(city_counts)
    cities = []
    for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
        info = city_info.get(city, {"icon": "📍", "info": "Tech hub."})
        cities.append({
            "icon": info["icon"],
            "name": city,
            "info": info["info"],
            "jobs": f"{count}/{total_jobs} jobs",
        })

    return {"items": cities}
