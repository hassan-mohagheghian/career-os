"""Resume/cover letter generation endpoints."""

from fastapi import APIRouter, Depends

from dependencies import get_resume_repo, get_resume_service, get_pending_generation_repo
from jobs.application.services.resume_service import ResumeService
from jobs.infrastructure import SQLAlchemyResumeRepository
from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
from shared.application.exceptions import NotFoundError

router = APIRouter()


@router.get("")
def list_resumes(repo: SQLAlchemyResumeRepository = Depends(get_resume_repo)):
    """List all resumes."""
    return repo.get_all()


@router.get("/active-generations")
def get_active_generations(repo: SQLAlchemyPendingGenerationRepository = Depends(get_pending_generation_repo)):
    """Get any active (queued/processing) resume or cover generations."""
    return repo.get_all_active()


@router.get("/{id}")
def get_resume(id: str, repo: SQLAlchemyResumeRepository = Depends(get_resume_repo)):
    """Get a resume by ID."""
    resume = repo.get_by_id(id)
    if not resume:
        raise NotFoundError(f"Resume {id} not found")
    return resume


@router.post("")
def create_resume(data: dict, service: ResumeService = Depends(get_resume_service)):
    """Save a new master resume as the next original_N version."""
    raw_text = data.get("raw_text") or data.get("content") or ""
    return service.upload_resume(raw_text, title=data.get("title"))


@router.put("/{id}")
def update_resume(id: str, data: dict, repo: SQLAlchemyResumeRepository = Depends(get_resume_repo)):
    """Update a resume."""
    existing = repo.get_by_id(id)
    if not existing:
        raise NotFoundError(f"Resume {id} not found")
    updates = {k: v for k, v in data.items() if k in ("title", "content")}
    if updates:
        updates["id"] = id
        repo.upsert(updates)
    return repo.get_by_id(id)


@router.delete("/{id}")
def delete_resume(id: str, repo: SQLAlchemyResumeRepository = Depends(get_resume_repo)):
    """Delete a resume."""
    deleted = repo.delete_by_id(id)
    if not deleted:
        raise NotFoundError(f"Resume {id} not found")
    return {"status": "deleted", "id": id}


@router.post("/{id}/generate-cover")
def generate_cover_letter(id: str, data: dict):
    """Generate a cover letter for a job."""
    return {"status": "started", "resume_id": id, "job_id": data.get("job_id")}
