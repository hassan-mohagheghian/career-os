"""Career intelligence endpoints."""

from fastapi import APIRouter, Depends

from dependencies import get_insight_repo, get_career_insight_run_repo
from infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
from infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
from infrastructure.workers.background import get_task_manager, generate_insights_task

router = APIRouter()


@router.get("")
def get_insights(repo: SQLAlchemyInsightRepository = Depends(get_insight_repo)):
    """Get all career insights."""
    return repo.get_all()


@router.get("/status")
def get_insights_status(repo: SQLAlchemyInsightRepository = Depends(get_insight_repo)):
    """Get section statuses."""
    return {"sections": repo.get_statuses()}


@router.get("/progress")
def get_insights_progress():
    """Get real-time insight generation progress."""
    manager = get_task_manager()
    running = manager.is_running("insights_all")
    return {"running": running, "status": "processing" if running else "idle"}


@router.get("/skills-intel")
def get_skills_intelligence(repo: SQLAlchemyInsightRepository = Depends(get_insight_repo)):
    """Get skills intelligence data."""
    result = repo.get_section("skills")
    if not result:
        return {"skills": [], "summary": None}
    return result


@router.post("/refresh")
async def refresh_insights():
    """Start generating all insight sections."""
    manager = get_task_manager()
    await manager.run("insights_all", generate_insights_task(None), name="insights_all")
    return {"status": "started"}


@router.post("/{section}/refresh")
async def refresh_insight_section(section: str):
    """Start generating a specific insight section."""
    manager = get_task_manager()
    task_id = f"insights_{section}"
    await manager.run(task_id, generate_insights_task(section), name=task_id)
    return {"status": "started", "section": section}


@router.get("/{section}")
def get_insight_section(section: str, repo: SQLAlchemyInsightRepository = Depends(get_insight_repo)):
    """Get a specific insight section."""
    result = repo.get_section(section)
    if not result:
        return {"section": section, "data": None}
    return result


@router.post("/cancel")
def cancel_insights():
    """Cancel insight generation."""
    manager = get_task_manager()
    manager.cancel("insights_all")
    return {"status": "cancelled"}
