"""LinkedIn profile endpoints — versioned upload/list/delete.

LinkedIn profiles are stored in the same `resumes` table with a `linkedin_N`
id. The latest version is what job analysis consumes as extra context.
"""

from fastapi import APIRouter, Depends

from dependencies import get_resume_repo, get_resume_service
from jobs.application.services.resume_service import ResumeService
from jobs.infrastructure import SQLAlchemyResumeRepository
from shared.application.exceptions import NotFoundError

router = APIRouter()


@router.get("")
def list_linkedin(repo: SQLAlchemyResumeRepository = Depends(get_resume_repo)):
    """List all LinkedIn profiles, newest version first."""
    return repo.list_linkedin()


@router.post("")
def create_linkedin(data: dict, service: ResumeService = Depends(get_resume_service)):
    """Save a new LinkedIn profile as the next linkedin_N version."""
    raw_text = data.get("raw_text") or ""
    return service.upload_linkedin(raw_text)


@router.get("/{id}")
def get_linkedin(id: str, repo: SQLAlchemyResumeRepository = Depends(get_resume_repo)):
    """Get a LinkedIn profile by ID."""
    profile = repo.get_by_id(id)
    if not profile:
        raise NotFoundError(f"LinkedIn profile {id} not found")
    return profile


@router.delete("/{id}")
def delete_linkedin(id: str, repo: SQLAlchemyResumeRepository = Depends(get_resume_repo)):
    """Delete a LinkedIn profile by ID."""
    deleted = repo.delete_by_id(id)
    if not deleted:
        raise NotFoundError(f"LinkedIn profile {id} not found")
    return {"status": "deleted", "id": id}
