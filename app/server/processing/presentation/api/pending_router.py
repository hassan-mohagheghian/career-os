"""Job processing queue endpoints."""

from fastapi import APIRouter, Depends

from dependencies import get_pending_repo
from processing.infrastructure import SQLAlchemyPendingRepository
from shared.application.exceptions import NotFoundError

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
def delete_pending(id: str, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Delete a pending job."""
    repo.delete(int(id), "pending_jobs")
    return {"status": "deleted", "id": id}


@router.post("/{id}/process")
def process_pending(id: str, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Enqueue a pending job for processing."""
    from shared.infrastructure.config.queue import get_queue_manager
    item = repo.get_by_id(id, "pending_jobs")
    if not item:
        raise NotFoundError(f"Pending job {id} not found")
    get_queue_manager().enqueue(int(id))
    return {"status": "queued", "id": id}


@router.post("/{id}/reset")
def reset_pending(id: str, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Reset a pending job."""
    from shared.infrastructure.config.queue import get_queue_manager
    get_queue_manager().reset_job(id, "pending_jobs")
    return {"status": "reset", "id": id}


@router.post("/process-all")
def process_all(repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Queue all created jobs for processing."""
    from shared.infrastructure.config.queue import get_queue_manager
    items = repo.list_pending("pending_jobs")
    ids = [i["id"] for i in items if i.get("status") == "created"]
    if ids:
        get_queue_manager().enqueue_bulk(ids)
    return {"queued": len(ids)}
