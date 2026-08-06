"""Company CRUD, intelligence, notes, links."""

import json

from fastapi import APIRouter, Depends, status as http_status
from fastapi.responses import Response

from dependencies import get_company_repo, get_company_intelligence_repo, get_company_link_repo, get_job_repo, get_processing_execution_repo
from companies.application.services.company_service import CompanyService
from companies.infrastructure import SQLAlchemyCompanyRepository, SQLAlchemyCompanyIntelligenceRepository, SQLAlchemyCompanyLinkRepository
from jobs.infrastructure import SQLAlchemyJobRepository
from processing.infrastructure import SQLAlchemyProcessingExecutionRepository
from shared.application.exceptions import NotFoundError

router = APIRouter()


def _queue_company_for_processing(company_id: str, exec_repo) -> str:
    """Create a COMPANY_PROCESSING execution and dispatch it to the worker queue.

    Mirrors the job intake flow: create execution → mark queued → enqueue TaskIQ.
    """
    from processing.domain.enums import ExecutionType
    from processing.application.use_cases.create_processing_execution import (
        CreateProcessingExecutionRequest,
        CreateProcessingExecutionUseCase,
    )
    from processing.application.services.dispatch_processing_execution import (
        DispatchProcessingExecutionService,
    )

    use_case = CreateProcessingExecutionUseCase(exec_repo)
    request = CreateProcessingExecutionRequest(
        execution_type=ExecutionType.COMPANY_PROCESSING,
        target_type="company",
        target_id=company_id,
    )
    response = use_case.execute(request)
    DispatchProcessingExecutionService(exec_repo).dispatch(response.execution_id)
    return response.execution_id


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
    id: str,
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


@router.post("", status_code=http_status.HTTP_201_CREATED)
def create_company(
    data: dict,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
    intel_repo: SQLAlchemyCompanyIntelligenceRepository = Depends(get_company_intelligence_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    """Create a company from intake (name + notes + links).

    When ``data.queue`` is true (default) the company is created and immediately
    queued for processing through the COMPANY_PROCESSING execution lifecycle.
    """
    service = CompanyService(repo, intel_repo)
    company = service.create_from_intake(
        name=data.get("name", ""),
        notes=data.get("notes") or [],
        links=data.get("links") or [],
        source=data.get("source", "web"),
        input_type=data.get("input_type", "url"),
    )
    if data.get("queue", True):
        execution_id = _queue_company_for_processing(company["id"], exec_repo)
        company["status"] = "queued"
        company["execution_id"] = execution_id
    return company


@router.put("/{id}")
def update_company(id: str, data: dict, repo: SQLAlchemyCompanyRepository = Depends(get_company_repo)):
    """Update a company."""
    company = repo.update(id, data)
    if not company:
        raise NotFoundError(f"Company {id} not found")
    return company


@router.delete("/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_company(
    id: str,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
    intel_repo: SQLAlchemyCompanyIntelligenceRepository = Depends(get_company_intelligence_repo),
    link_repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    """Hard-delete a company and its related tables and executions."""
    company = repo.get_by_id(id)
    if not company:
        raise NotFoundError(f"Company {id} not found")
    exec_repo.delete_by_target("company", id)
    link_repo.delete_by_company_id(id)
    intel_repo.delete_by_company_id(id)
    if not repo.delete(id):
        raise NotFoundError(f"Company {id} not found")
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@router.get("/{id}/intelligence")
def get_company_intelligence(id: str, repo: SQLAlchemyCompanyIntelligenceRepository = Depends(get_company_intelligence_repo)):
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
def get_company_jobs(id: str, job_repo: SQLAlchemyJobRepository = Depends(get_job_repo)):
    """Get jobs linked to this company."""
    return job_repo.get_jobs_by_company_id(id)


@router.get("/{id}/links")
def get_company_links(id: str, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Get all links for a company."""
    return repo.get_by_company_id(id)


@router.post("/{id}/links")
def add_company_link(id: str, data: dict, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Add a link to a company."""
    return repo.create(id, data.get("url", ""), data.get("title", ""), data.get("description", ""))


@router.delete("/{id}/links/{link_id}")
def delete_company_link(id: str, link_id: int, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Delete a company link."""
    repo.delete(link_id, id)
    return {"status": "deleted"}


@router.post("/{id}/notes")
def add_note(id: str, data: dict, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Add a note to a company."""
    content = data.get("content", "")
    repo.create(id, "", f"note:{content}")
    return {"status": "created"}


@router.get("/{id}/notes")
def get_company_notes(id: str, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Get all notes for a company."""
    links = repo.get_by_company_id(id)
    return [l for l in links if l.get("title", "").startswith("note:")]


@router.delete("/{id}/notes/{note_id}")
def delete_company_note(id: str, note_id: int, repo: SQLAlchemyCompanyLinkRepository = Depends(get_company_link_repo)):
    """Delete a company note."""
    repo.delete(note_id, id)
    return {"status": "deleted"}
