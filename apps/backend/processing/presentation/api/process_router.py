from fastapi import APIRouter, Depends, status as http_status

from dependencies import get_job_repo, get_processing_execution_repo
from jobs.infrastructure import SQLAlchemyJobRepository
from processing.infrastructure import SQLAlchemyProcessingExecutionRepository
from processing.domain.enums import ExecutionType, ExecutionStatus
from processing.application.use_cases.create_processing_execution import (
    CreateProcessingExecutionRequest,
    CreateProcessingExecutionUseCase,
)
from processing.application.services.dispatch_processing_execution import (
    DispatchProcessingExecutionService,
)
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

    use_case = CreateProcessingExecutionUseCase(exec_repo)
    request = CreateProcessingExecutionRequest(
        execution_type=ExecutionType.JOB_PROCESSING,
        target_type="job",
        target_id=target_id,
    )
    response = use_case.execute(request)

    DispatchProcessingExecutionService(exec_repo).dispatch(response.execution_id)
    return ProcessJobResponse(execution_id=response.execution_id, status=ExecutionStatus.QUEUED.value)
