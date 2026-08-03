"""Company CRUD, intelligence, notes, links."""

import json

from fastapi import APIRouter, Depends

from dependencies import get_company_repo, get_company_link_repo, get_company_intelligence_repo, get_job_repo
from companies.infrastructure import SQLAlchemyCompanyRepository, SQLAlchemyCompanyIntelligenceRepository, SQLAlchemyCompanyLinkRepository
from jobs.infrastructure import SQLAlchemyJobRepository
from shared.application.exceptions import NotFoundError

router = APIRouter()


@router.get("")
def list_companies(
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
    intel_repo: SQLAlchemyCompanyIntelligenceRepository = Depends(get_company_intelligence_repo),
):
    """List all companies with intelligence scores."""
    companies = repo.list_all()
    for c in companies:
        intel = intel_repo.get_by_company_id(c["id"])
        if intel and intel.get("scores"):
            try:
                c["scores"] = json.loads(intel["scores"])
            except (json.JSONDecodeError, TypeError):
                c["scores"] = {}
        else:
            c["scores"] = {}
    return companies


@router.get("/{id}")
def get_company(
    id: int,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
    intel_repo: SQLAlchemyCompanyIntelligenceRepository = Depends(get_company_intelligence_repo),
    job_repo: SQLAlchemyJobRepository = Depends(get_job_repo),
):
    """Get a company by ID with intelligence and linked jobs."""
    company = repo.get_by_id(id)
    if not company:
        raise NotFoundError(f"Company {id} not found")

    intel = intel_repo.get_by_company_id(id)
    if intel:
        for field in ["overview", "culture_analysis", "international_analysis", "career_analysis",
                       "benefits_analysis", "visa_analysis", "technology_analysis", "recommendation",
                       "scores", "raw_source_data"]:
            if intel.get(field) and isinstance(intel[field], str):
                try:
                    intel[field] = json.loads(intel[field])
                except (json.JSONDecodeError, TypeError):
                    pass
    company["intelligence"] = intel

    jobs = job_repo.get_jobs_by_company_id(id)
    company["jobs"] = [{k: j[k] for k in ["id", "company", "role", "location", "match", "score", "fit_score", "success_score", "overall_score"] if k in j} for j in jobs]

    return company


@router.post("")
def create_company(data: dict, repo: SQLAlchemyCompanyRepository = Depends(get_company_repo)):
    """Create a new company."""
    return repo.create(data)


@router.put("/{id}")
def update_company(id: int, data: dict, repo: SQLAlchemyCompanyRepository = Depends(get_company_repo)):
    """Update a company."""
    company = repo.update(id, data)
    if not company:
        raise NotFoundError(f"Company {id} not found")
    return company


@router.delete("/{id}")
def delete_company(id: int, repo: SQLAlchemyCompanyRepository = Depends(get_company_repo)):
    """Delete a company."""
    repo.delete(id)
    return {"status": "deleted", "id": id}


@router.get("/{id}/intelligence")
def get_company_intelligence(id: int, repo: SQLAlchemyCompanyIntelligenceRepository = Depends(get_company_intelligence_repo)):
    """Get company intelligence."""
    intel = repo.get_by_company_id(id)
    if not intel:
        return {"company_id": id, "overview": None}
    for field in ["overview", "culture_analysis", "international_analysis", "career_analysis",
                   "benefits_analysis", "visa_analysis", "technology_analysis", "recommendation",
                   "scores", "raw_source_data"]:
        if intel.get(field) and isinstance(intel[field], str):
            try:
                intel[field] = json.loads(intel[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return intel


@router.get("/{id}/jobs")
def get_company_jobs(id: int, job_repo: SQLAlchemyJobRepository = Depends(get_job_repo)):
    """Get jobs linked to this company."""
    return job_repo.get_jobs_by_company_id(id)


@router.get("/{id}/links")
def get_company_links(id: int, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Get all links for a company."""
    return repo.get_by_company_id(id)


@router.post("/{id}/links")
def add_company_link(id: int, data: dict, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Add a link to a company."""
    return repo.create(id, data.get("url", ""), data.get("title", ""), data.get("description", ""))


@router.delete("/{id}/links/{link_id}")
def delete_company_link(id: int, link_id: int, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Delete a company link."""
    repo.delete(link_id, id)
    return {"status": "deleted"}


@router.post("/{id}/notes")
def add_note(id: int, data: dict, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Add a note to a company."""
    content = data.get("content", "")
    repo.create(id, "", f"note:{content}")
    return {"status": "created"}


@router.get("/{id}/notes")
def get_company_notes(id: int, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Get all notes for a company."""
    links = repo.get_by_company_id(id)
    return [l for l in links if l.get("title", "").startswith("note:")]


@router.delete("/{id}/notes/{note_id}")
def delete_company_note(id: int, note_id: int, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Delete a company note."""
    repo.delete(note_id, id)
    return {"status": "deleted"}
