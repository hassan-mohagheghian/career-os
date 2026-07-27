"""Skill roadmap endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from dependencies import get_skill_roadmap_repo, get_skill_roadmap_progress_repo, get_skill_roadmap_job_repo
from infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
from infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
from infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
from exceptions import NotFoundError

router = APIRouter()


def build_roadmap_tree(rows: list[dict]) -> list[dict]:
    """Build a nested tree structure from flat database rows with parent_id."""
    nodes_by_id = {}
    for r in rows:
        node = dict(r)
        node["children"] = []
        nodes_by_id[node["id"]] = node

    roots = []
    for node in nodes_by_id.values():
        parent_id = node.get("parent_id")
        if parent_id and parent_id in nodes_by_id:
            nodes_by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


@router.get("")
def list_roadmaps(
    skill: Optional[str] = Query(None),
    repo: SQLAlchemySkillRoadmapRepository = Depends(get_skill_roadmap_repo),
):
    """List all skill roadmaps or return nested tree for a specific skill."""
    if skill:
        rows = repo.get_by_skill_name(skill)
        tree = build_roadmap_tree(rows)
        max_version = max((r.get("version") or 1 for r in rows), default=1)
        latest_updated = max((r.get("created_at") or "" for r in rows), default=None)
        return {
            "skill_name": skill,
            "roadmap": tree,
            "version": max_version,
            "updated_at": latest_updated,
        }
    return repo.get_all()


@router.get("/progress")
def get_roadmap_job_progress(
    skill: Optional[str] = Query(None),
    repo: SQLAlchemySkillRoadmapJobRepository = Depends(get_skill_roadmap_job_repo),
):
    """Get latest job status for a skill roadmap generation."""
    if not skill:
        return repo.get_all()
    row = repo.get_latest_for_skill(skill)
    if not row:
        return {"status": "idle", "skill_name": skill}
    return row


@router.get("/jobs")
def get_roadmap_jobs(
    skill: Optional[str] = Query(None),
    limit: int = 20,
    repo: SQLAlchemySkillRoadmapJobRepository = Depends(get_skill_roadmap_job_repo),
):
    """Get all roadmap jobs, optionally filtered by skill."""
    if skill:
        items = repo.get_for_skill(skill, limit)
    else:
        items = repo.get_all(limit)
    return {"items": items}


@router.get("/progress/all")
def get_all_progress(repo: SQLAlchemySkillRoadmapProgressRepository = Depends(get_skill_roadmap_progress_repo)):
    """Get all roadmap progress."""
    return repo.get_all()


@router.get("/{id}")
def get_roadmap(id: int, repo: SQLAlchemySkillRoadmapRepository = Depends(get_skill_roadmap_repo)):
    """Get a roadmap by ID."""
    row = repo.get_by_id(id)
    if not row:
        raise NotFoundError(f"Roadmap {id} not found")
    return row


@router.post("/generate")
async def generate_roadmap(data: dict):
    """Start AI roadmap generation."""
    skill_name = data.get("skill_name", "")

    async def _run_generate(skill_name: str):
        from services.skill_roadmap_service import generate_roadmap
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, generate_roadmap, skill_name)

    manager = get_task_manager()
    task_id = f"roadmap_generate_{skill_name}"
    await manager.run(task_id, _run_generate(skill_name), name=task_id)
    return {"status": "started", "skill_name": skill_name}


@router.post("/extend")
async def extend_roadmap(data: dict):
    """Extend a roadmap with more detail."""
    skill_name = data.get("skill_name", "")

    async def _run_extend(skill_name: str):
        from services.skill_roadmap_service import extend_roadmap
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, extend_roadmap, skill_name)

    manager = get_task_manager()
    task_id = f"roadmap_extend_{skill_name}"
    await manager.run(task_id, _run_extend(skill_name), name=task_id)
    return {"status": "started", "skill_name": skill_name}


@router.post("/finegrain")
async def finegrain_roadmap(data: dict):
    """Fine-grain a roadmap node."""
    skill_name = data.get("skill_name", "")

    async def _run_finegrain(skill_name: str):
        from services.skill_roadmap_service import finegrain_roadmap
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, finegrain_roadmap, skill_name)

    manager = get_task_manager()
    task_id = f"roadmap_finegrain_{skill_name}"
    await manager.run(task_id, _run_finegrain(skill_name), name=task_id)
    return {"status": "started", "skill_name": skill_name}


@router.post("/cancel")
def cancel_roadmap(skill: str = Query(...)):
    """Cancel roadmap generation for a skill."""
    manager = get_task_manager()
    manager.cancel(f"roadmap_generate_{skill}")
    manager.cancel(f"roadmap_extend_{skill}")
    manager.cancel(f"roadmap_finegrain_{skill}")
    return {"status": "cancelled", "skill_name": skill}


# Lazy import to avoid circular
def get_task_manager():
    from infrastructure.workers.background import get_task_manager as _get
    return _get()
