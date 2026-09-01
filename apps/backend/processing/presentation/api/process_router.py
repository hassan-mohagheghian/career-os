from fastapi import APIRouter, Depends, status as http_status

from dependencies import get_job_repo, get_processing_execution_repo
from jobs.infrastructure import SQLAlchemyJobRepository
from processing.infrastructure import SQLAlchemyProcessingExecutionRepository
from processing.domain.enums import ExecutionStatus
from processing.application.services.execution_actions import ExecutionActionService
from processing.presentation.api.schemas.process_job import ProcessJobResponse
from shared.application.exceptions import NotFoundError

router = APIRouter()


@router.post("/{jobId}/process", status_code=http_status.HTTP_202_ACCEPTED, response_model=ProcessJobResponse)
def process_job(
    jobId: str,
    job_repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    job = job_repo.get_by_id(jobId)
    if not job:
        raise NotFoundError(f"Job {jobId} not found")

    # New processing features reference jobs by their UUID `id`.
    target_id = job.get("id") or str(jobId)

    result = ExecutionActionService(exec_repo, user_id=job_repo._user_id).reprocess("job", target_id)
    return ProcessJobResponse(execution_id=result["execution_id"], status=ExecutionStatus.QUEUED.value)
