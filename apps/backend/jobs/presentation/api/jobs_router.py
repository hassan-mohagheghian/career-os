"""Job creation and generation routes.

Job listing, detail, and lifecycle endpoints were removed: the V2 jobs list
uses GET /jobs/list (jobs_v2_router) and POST /jobs/{id}/process
(process_router). The retained endpoints below back the AddJobDrawer
(create_job) and the resume feature (generate-resume / generate-cover).
"""

import json
import threading
from fastapi import APIRouter, Depends
from fastapi import status as http_status

from dependencies import get_job_repo, get_session_sync, get_processing_execution_repo

from jobs.infrastructure import SQLAlchemyJobRepository
from jobs.infrastructure.repositories.sa_tailored_document_repository import SQLAlchemyTailoredDocumentRepository
from processing.infrastructure import SQLAlchemyProcessingExecutionRepository

from shared.application.exceptions import NotFoundError, BadRequestError, JobAlreadyExistsError

from jobs.presentation.api.schemas.jobs import CreateJobRequest, CreateJobResponse

router = APIRouter()


def _queue_job_for_processing(job_id: str, exec_repo) -> str:
    """Create a JOB_PROCESSING execution and dispatch it to the worker queue.

    Returns the created execution id. Mirrors the ``process_job`` endpoint so a
    job created with ``queue=true`` follows the exact same instant processing
    workflow (create execution → mark queued → enqueue TaskIQ task).
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
        execution_type=ExecutionType.JOB_PROCESSING,
        target_type="job",
        target_id=job_id,
    )
    response = use_case.execute(request)
    DispatchProcessingExecutionService(exec_repo).dispatch(response.execution_id)
    return response.execution_id


@router.post("", status_code=http_status.HTTP_201_CREATED, response_model=CreateJobResponse)
def create_job(
    body: CreateJobRequest,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    """Create a new job from a job posting URL.

    When ``body.queue`` is true the job is created and immediately queued for
    processing (the same workflow triggered by ``POST /api/jobs/{id}/process``).
    Otherwise the job is created with status ``imported`` and stays idle.
    """
    existing = repo.get_by_url(body.job_post_url)
    if existing and not existing.get("deleted"):
        raise JobAlreadyExistsError(job_id=existing.get("id"))

    links_json = json.dumps([l.model_dump() for l in body.links], ensure_ascii=False)
    notes_json = json.dumps([n.model_dump() for n in body.notes], ensure_ascii=False)

    job = repo.create_job(
        url=body.job_post_url,
        title=body.job_title,
        notes=notes_json,
        links=links_json,
    )

    if body.queue:
        execution_id = _queue_job_for_processing(job["id"], exec_repo)
        return CreateJobResponse(id=job["id"], status="queued", execution_id=execution_id)

    return CreateJobResponse(id=job["id"], status=job["status"])


@router.post("/{job_id}/generate-resume")
def generate_resume(job_id: str, session = Depends(get_session_sync)):
    """Start background resume generation for a job."""
    repo = SQLAlchemyJobRepository(session)
    job = repo.get_by_id(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")

    doc_repo = SQLAlchemyTailoredDocumentRepository(session)
    running = doc_repo.get_active_for_job(job_id,"resume")
    if running:
        raise BadRequestError("A resume generation is already running for this job")

    gen = doc_repo.create_generation(job_id,"resume")
    gen_id = gen["id"]
    session.commit()

    def _run():
        from jobs.infrastructure.workers.generation_worker import process_generation
        try:
            process_generation(gen_id)
        except Exception as e:
            from shared.infrastructure.process.logging_config import get_logger
            get_logger('jobs').error("Generation failed", gen_id=gen_id, error=str(e))

    threading.Thread(target=_run, daemon=True).start()
    return {"gen_id": gen_id, "status": "queued", "job_id": job_id}


@router.post("/{job_id}/generate-cover")
def generate_cover(job_id: str, session = Depends(get_session_sync)):
    """Start background cover letter generation for a job."""
    repo = SQLAlchemyJobRepository(session)
    job = repo.get_by_id(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")

    doc_repo = SQLAlchemyTailoredDocumentRepository(session)
    running = doc_repo.get_active_for_job(job_id,"cover")
    if running:
        raise BadRequestError("A cover letter generation is already running for this job")

    gen = doc_repo.create_generation(job_id,"cover")
    gen_id = gen["id"]
    session.commit()

    def _run():
        from jobs.infrastructure.workers.generation_worker import process_generation
        try:
            process_generation(gen_id)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
    return {"gen_id": gen_id, "status": "queued", "job_id": job_id}
