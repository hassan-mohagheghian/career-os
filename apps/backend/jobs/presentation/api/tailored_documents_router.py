"""Tailored document (resume/cover letter) generation and management endpoints."""

from dependencies import get_pending_generation_repo
from fastapi import APIRouter, Depends

from jobs.infrastructure.repositories.sa_tailored_document_repository import SQLAlchemyTailoredDocumentRepository
from shared.application.exceptions import NotFoundError

router = APIRouter()


@router.get("")
def list_tailored_documents(repo: SQLAlchemyTailoredDocumentRepository = Depends(get_pending_generation_repo)):
    """List all tailored documents."""
    return repo.get_all()


@router.get("/active-generations")
def get_active_generations(repo: SQLAlchemyTailoredDocumentRepository = Depends(get_pending_generation_repo)):
    """Get any active (queued/processing) resume or cover generations."""
    return repo.get_all_active()


@router.get("/{id}")
def get_tailored_document(id: str, repo: SQLAlchemyTailoredDocumentRepository = Depends(get_pending_generation_repo)):
    """Get a tailored document by ID."""
    doc = repo.get_by_id(id)
    if not doc:
        raise NotFoundError(f"Document {id} not found")
    return doc


@router.post("")
def create_tailored_document(data: dict, repo: SQLAlchemyTailoredDocumentRepository = Depends(get_pending_generation_repo)):
    """Create a new tailored document."""
    import uuid
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    return repo.upsert({
        "id": doc_id,
        "title": data.get("title", "Original"),
        "content": data.get("content", ""),
    })


@router.put("/{id}")
def update_tailored_document(id: str, data: dict, repo: SQLAlchemyTailoredDocumentRepository = Depends(get_pending_generation_repo)):
    """Update a tailored document."""
    existing = repo.get_by_id(id)
    if not existing:
        raise NotFoundError(f"Document {id} not found")
    updates = {k: v for k, v in data.items() if k in ("title", "content")}
    if updates:
        updates["id"] = id
        repo.upsert(updates)
    return repo.get_by_id(id)


@router.delete("/{id}")
def delete_tailored_document(id: str, repo: SQLAlchemyTailoredDocumentRepository = Depends(get_pending_generation_repo)):
    """Delete a tailored document."""
    repo.delete_by_id(id)
    return {"status": "deleted", "id": id}


@router.post("/{id}/generate-cover")
def generate_cover_letter(id: str, data: dict):
    """Generate a cover letter for a job."""
    return {"status": "started", "resume_id": id, "job_num": data.get("job_num")}
