"""Skill roadmap endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from dependencies import get_db
from exceptions import NotFoundError
from infrastructure.workers.background import get_task_manager

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
def list_roadmaps(skill: Optional[str] = Query(None), db=Depends(get_db)):
    """List all skill roadmaps or return nested tree for a specific skill."""
    if skill:
        rows = db.execute(
            "SELECT * FROM skill_roadmaps WHERE LOWER(skill_name) = LOWER(?) ORDER BY sort_order, id",
            (skill,),
        ).fetchall()
        row_dicts = [dict(r) for r in rows]
        tree = build_roadmap_tree(row_dicts)

        max_version = max((r.get("version") or 1 for r in row_dicts), default=1)
        latest_updated = max((r.get("created_at") or "" for r in row_dicts), default=None)

        return {
            "skill_name": skill,
            "roadmap": tree,
            "version": max_version,
            "updated_at": latest_updated,
        }

    rows = db.execute("SELECT * FROM skill_roadmaps ORDER BY skill_name").fetchall()
    return [dict(r) for r in rows]


@router.get("/progress")
def get_roadmap_job_progress(skill: Optional[str] = Query(None), db=Depends(get_db)):
    """Get latest job status for a skill roadmap generation."""
    if not skill:
        rows = db.execute("SELECT * FROM skill_roadmap_jobs ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    row = db.execute(
        "SELECT * FROM skill_roadmap_jobs WHERE LOWER(skill_name) = LOWER(?) ORDER BY created_at DESC LIMIT 1",
        (skill,),
    ).fetchone()
    if not row:
        return {"status": "idle", "skill_name": skill}
    return dict(row)


@router.get("/progress/all")
def get_all_progress(db=Depends(get_db)):
    """Get all roadmap progress."""
    rows = db.execute("SELECT * FROM skill_roadmap_progress").fetchall()
    return [dict(r) for r in rows]


@router.get("/{id}")
def get_roadmap(id: int, db=Depends(get_db)):
    """Get a roadmap by ID."""
    row = db.execute("SELECT * FROM skill_roadmaps WHERE id=?", (id,)).fetchone()
    if not row:
        raise NotFoundError(f"Roadmap {id} not found")
    return dict(row)


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


@router.post("/{skill_name}/cancel")
def cancel_roadmap(skill_name: str):
    """Cancel roadmap generation."""
    manager = get_task_manager()
    manager.cancel(f"roadmap_generate_{skill_name}")
    manager.cancel(f"roadmap_extend_{skill_name}")
    manager.cancel(f"roadmap_finegrain_{skill_name}")
    return {"status": "cancelled", "skill_name": skill_name}
