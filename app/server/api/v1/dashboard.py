"""Dashboard data, generation history, cities."""

import json

from fastapi import APIRouter, Depends, Query

from dependencies import get_db

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(db=Depends(get_db)):
    """Get dashboard summary data."""
    jobs_total = db.execute("SELECT COUNT(*) FROM jobs WHERE deleted=0").fetchone()[0]
    jobs_high = db.execute("SELECT COUNT(*) FROM jobs WHERE deleted=0 AND match='High'").fetchone()[0]
    companies_total = db.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    skills_total = db.execute("SELECT COUNT(*) FROM skills WHERE hidden=0").fetchone()[0]
    pending_count = db.execute("SELECT COUNT(*) FROM pending_jobs WHERE status != 'done'").fetchone()[0]

    return {
        "jobs_total": jobs_total,
        "jobs_high_match": jobs_high,
        "companies_total": companies_total,
        "skills_total": skills_total,
        "pending_count": pending_count,
        "recent_activity": [],
    }


@router.get("/generation-history")
def get_generation_history(db=Depends(get_db), limit: int = 50, offset: int = 0):
    """Get unified generation history from ALL sources:
    pending_jobs, pending_companies, pending_generations, skill_roadmap_jobs, career_insight_runs.
    """
    from services.process.generation_repository import GenerationHistoryRepository

    repo = GenerationHistoryRepository(db)
    result = repo.get_all(limit=limit, offset=offset)

    return {
        "items": [item.to_dict() for item in result['items']],
        "total": result['total'],
        "offset": offset,
        "limit": limit,
    }


@router.get("/local-history")
def get_local_history(
    context: str = Query(..., description="Context: job, company, skill, insight"),
    job_num: int | None = Query(None),
    company_id: int | None = Query(None),
    skill_name: str | None = Query(None),
    insight_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
):
    """Get local generation history filtered by context."""
    from services.process.generation_repository import GenerationHistoryRepository

    repo = GenerationHistoryRepository(db)

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


@router.get("/local-history/active")
def get_local_active_count(
    context: str = Query(...),
    job_num: int | None = Query(None),
    company_id: int | None = Query(None),
    skill_name: str | None = Query(None),
    insight_type: str | None = Query(None),
    db=Depends(get_db),
):
    """Get count of currently running/queued items for a context."""
    from services.process.generation_repository import GenerationHistoryRepository

    repo = GenerationHistoryRepository(db)
    count = repo.get_active_count(
        context,
        job_num=job_num,
        company_id=company_id,
        skill_name=skill_name,
        insight_type=insight_type,
    )
    return {'active_count': count}


@router.get("/cities")
def get_cities(db=Depends(get_db)):
    """Get all unique cities with job counts."""
    rows = db.execute(
        "SELECT location, locations FROM jobs WHERE deleted=0"
    ).fetchall()

    city_counts = {}
    for row in rows:
        r = dict(row)
        locations = []
        if r.get("locations"):
            try:
                locations = (
                    json.loads(r["locations"])
                    if isinstance(r["locations"], str)
                    else r["locations"]
                )
            except (json.JSONDecodeError, TypeError):
                pass
        if not locations and r.get("location"):
            locations = [r["location"]]
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
