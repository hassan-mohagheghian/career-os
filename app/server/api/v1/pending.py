"""Job processing queue endpoints."""

from fastapi import APIRouter, Depends

from dependencies import get_pending_repo
from infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
from exceptions import NotFoundError

router = APIRouter()


@router.get("")
def list_pending(repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """List pending jobs."""
    return repo.list_pending("pending_jobs")


@router.post("")
def create_pending(data: dict, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Queue a new job for processing."""
    return repo.create(data, "pending_jobs")


@router.get("/{id}")
def get_pending(id: str, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Get a pending job."""
    item = repo.get_by_id(id, "pending_jobs")
    if not item:
        raise NotFoundError(f"Pending job {id} not found")
    return item


@router.delete("/{id}")
def cancel_pending(id: str, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Cancel a pending job."""
    from core.queue import get_queue_manager
    get_queue_manager().cancel_job(id, "pending_jobs")
    return {"status": "cancelled", "id": id}


@router.post("/{id}/reset")
def reset_pending(id: str, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Reset a pending job."""
    from core.queue import get_queue_manager
    get_queue_manager().reset_job(id, "pending_jobs")
    return {"status": "reset", "id": id}


@router.post("/queue-all")
def queue_all(repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Queue all pending jobs."""
    count = repo.count_pending("pending_jobs")
    return {"queued": count}
