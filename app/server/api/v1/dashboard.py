"""Dashboard data, generation history, cities."""

import json

from fastapi import APIRouter, Depends

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
    """Get generation history from pending_generations table."""
    # Try pending_generations first (real data), fall back to generation_history
    for table in ["pending_generations", "generation_history"]:
        try:
            total = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            rows = db.execute(
                f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return {"items": [dict(r) for r in rows], "total": total, "offset": offset, "limit": limit}
        except Exception:
            continue
    return {"items": [], "total": 0, "offset": offset, "limit": limit}


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
