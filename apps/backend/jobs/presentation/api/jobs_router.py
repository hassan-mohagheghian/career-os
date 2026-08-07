"""Job creation routes.

Job listing, detail, and lifecycle endpoints were removed: the V2 jobs list
uses GET /jobs/list (jobs_v2_router) and POST /jobs/{id}/process
(process_router). The retained endpoint below backs the AddJobDrawer
(create_job). Resume / cover-letter generation was removed with the legacy
tailored-generation stack.
"""

import json
from fastapi import APIRouter, Depends
from fastapi import status as http_status

from dependencies import get_job_repo, get_processing_execution_repo

from jobs.infrastructure import SQLAlchemyJobRepository
from processing.infrastructure import SQLAlchemyProcessingExecutionRepository

from shared.application.exceptions import JobAlreadyExistsError

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
