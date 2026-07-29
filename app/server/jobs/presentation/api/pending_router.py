"""Job processing queue endpoints."""

from fastapi import APIRouter, Depends

from dependencies import get_pending_repo
from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
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
    from shared.infrastructure.queue.arq_client import enqueue_job_sync
    item = repo.get_by_id(id, "pending_jobs")
    if not item:
        raise NotFoundError(f"Pending job {id} not found")
    enqueue_job_sync(int(id))
    return {"status": "queued", "id": id}


@router.post("/{id}/reset")
def reset_pending(id: str, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Reset a pending job."""
    repo.update_fields(int(id), table="pending_jobs", status='pending', error=None,
        current_node=None, progress_pct=0, retry_count=0,
        failure_reason=None, failure_step=None, failure_timestamp=None)
    return {"status": "reset", "id": id}


@router.post("/process-all")
def process_all(repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Queue all created jobs for processing."""
    from shared.infrastructure.queue.arq_client import enqueue_job_sync
    items = repo.list_pending("pending_jobs")
    ids = [i["id"] for i in items if i.get("status") == "created"]
    for pid in ids:
        enqueue_job_sync(pid)
    return {"queued": len(ids)}
