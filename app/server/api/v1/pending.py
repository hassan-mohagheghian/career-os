"""Job processing queue endpoints."""

import sqlite3

from fastapi import APIRouter, Depends

from dependencies import get_db
from infrastructure.database.pending_repository import PendingRepository
from exceptions import NotFoundError

router = APIRouter()


def _get_repo(db: sqlite3.Connection = Depends(get_db)) -> PendingRepository:
    return PendingRepository(db)


@router.get("")
def list_pending(repo: PendingRepository = Depends(_get_repo)):
    """List pending jobs."""
    items = repo.list_pending("pending_jobs")
    return items


@router.post("")
def create_pending(data: dict, repo: PendingRepository = Depends(_get_repo)):
    """Queue a new job for processing."""
    return repo.create(data, "pending_jobs")


@router.get("/{id}")
def get_pending(id: str, repo: PendingRepository = Depends(_get_repo)):
    """Get a pending job."""
    item = repo.get_by_id(id, "pending_jobs")
    if not item:
        raise NotFoundError(f"Pending job {id} not found")
    return item


@router.delete("/{id}")
def cancel_pending(id: str, repo: PendingRepository = Depends(_get_repo)):
    """Cancel a pending job."""
    from core.queue import get_queue_manager
    get_queue_manager().cancel_job(id, "pending_jobs")
    return {"status": "cancelled", "id": id}


@router.post("/{id}/reset")
def reset_pending(id: str, repo: PendingRepository = Depends(_get_repo)):
    """Reset a pending job."""
    from core.queue import get_queue_manager
    get_queue_manager().reset_job(id, "pending_jobs")
    return {"status": "reset", "id": id}


@router.post("/queue-all")
def queue_all(repo: PendingRepository = Depends(_get_repo)):
    """Queue all pending jobs."""
    count = repo.count_pending("pending_jobs")
    return {"queued": count}
