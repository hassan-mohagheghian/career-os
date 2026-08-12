"""Applications API router — the Job Application Workspace backend.

Owned by the Applications bounded context (per-context router, rule 10). Reads
and writes application records and dispatches generation executions (tailored
resume, cover letter, AI roadmap) through the processing pipeline.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status as http_status
from fastapi import Response
from fastapi.responses import JSONResponse

from applications.application.services.application_service import ApplicationService
from applications.application.services.document_service import DocumentService
from applications.application.services.follow_up_service import FollowUpService
from applications.domain.entities.application import ApplicationStatus, DocumentType
from applications.infrastructure import (
    SQLAlchemyApplicationRepository,
    SQLAlchemyDocumentRepository,
    SQLAlchemyFollowUpRepository,
)
from applications.presentation.api.schemas.applications import (
    ApplicationDetailResponse,
    ApplicationDocumentSchema,
    ApplicationFollowUpSchema,
    CreateApplicationRequest,
    CreateFollowUpRequest,
    DeleteResponse,
    GenerateResponse,
    UpdateApplicationRequest,
    UpdateDocumentRequest,
    UpdateFollowUpRequest,
    build_detail_response,
)
from dependencies import (
    get_application_repo,
    get_application_service,
    get_document_repo,
    get_document_service,
    get_follow_up_repo,
    get_follow_up_service,
    get_processing_execution_repo,
)
from processing.application.services.dispatch_processing_execution import (
    DispatchProcessingExecutionService,
)
from processing.application.use_cases.create_processing_execution import (
    CreateProcessingExecutionRequest,
    CreateProcessingExecutionUseCase,
)
from processing.domain.enums import ExecutionType
from processing.infrastructure import SQLAlchemyProcessingExecutionRepository
from shared.application.exceptions import BadRequestError, NotFoundError

router = APIRouter()

_EXECUTION_TYPE_BY_DOCUMENT = {
    DocumentType.TAILORED_RESUME: ExecutionType.APPLICATION_RESUME,
    DocumentType.COVER_LETTER: ExecutionType.APPLICATION_COVER_LETTER,
}


def _detail(
    application_repo: SQLAlchemyApplicationRepository,
    follow_up_repo: SQLAlchemyFollowUpRepository,
    document_repo: SQLAlchemyDocumentRepository,
    application_id: str,
) -> ApplicationDetailResponse:
    application = application_repo.get_by_id(application_id)
    if not application:
        raise NotFoundError(f"Application {application_id} not found")
    return build_detail_response(
        application,
        follow_up_repo.list_for_application(application_id),
        document_repo.list_for_application(application_id),
    )


def _dispatch(exec_repo: SQLAlchemyProcessingExecutionRepository, execution_type: ExecutionType, application_id: str) -> str:
    use_case = CreateProcessingExecutionUseCase(exec_repo)
    request = CreateProcessingExecutionRequest(
        execution_type=execution_type,
        target_type="application",
        target_id=application_id,
    )
    response = use_case.execute(request)
    DispatchProcessingExecutionService(exec_repo).dispatch(response.execution_id)
    return response.execution_id


@router.get("/by-job/{job_id}", response_model=ApplicationDetailResponse)
def get_application_by_job(
    job_id: str,
    application_repo: SQLAlchemyApplicationRepository = Depends(get_application_repo),
    follow_up_repo: SQLAlchemyFollowUpRepository = Depends(get_follow_up_repo),
    document_repo: SQLAlchemyDocumentRepository = Depends(get_document_repo),
):
    application = application_repo.get_by_job_id(job_id)
    if not application:
        raise NotFoundError(f"No application found for job {job_id}")
    return build_detail_response(
        application,
        follow_up_repo.list_for_application(application["id"]),
        document_repo.list_for_application(application["id"]),
    )


@router.post("", status_code=http_status.HTTP_201_CREATED, response_model=ApplicationDetailResponse)
def create_application(
    body: CreateApplicationRequest,
    service: ApplicationService = Depends(get_application_service),
    follow_up_repo: SQLAlchemyFollowUpRepository = Depends(get_follow_up_repo),
    document_repo: SQLAlchemyDocumentRepository = Depends(get_document_repo),
):
    stored = service.create(body.job_id)
    return build_detail_response(
        stored,
        follow_up_repo.list_for_application(stored["id"]),
        document_repo.list_for_application(stored["id"]),
    )


@router.patch("/{application_id}", response_model=ApplicationDetailResponse)
def update_application(
    application_id: str,
    body: UpdateApplicationRequest,
    service: ApplicationService = Depends(get_application_service),
    application_repo: SQLAlchemyApplicationRepository = Depends(get_application_repo),
    follow_up_repo: SQLAlchemyFollowUpRepository = Depends(get_follow_up_repo),
    document_repo: SQLAlchemyDocumentRepository = Depends(get_document_repo),
):
    data = body.model_dump(exclude_unset=True)
    service.update(application_id, data)
    return _detail(
        application_repo,
        follow_up_repo,
        document_repo,
        application_id,
    )


@router.post("/{application_id}/follow-ups", status_code=http_status.HTTP_201_CREATED, response_model=ApplicationFollowUpSchema)
def add_follow_up(
    application_id: str,
    body: CreateFollowUpRequest,
    service: FollowUpService = Depends(get_follow_up_service),
):
    return service.add(application_id, body.scheduled_at, body.note)


@router.patch("/follow-ups/{follow_up_id}", response_model=ApplicationFollowUpSchema)
def update_follow_up(
    follow_up_id: str,
    body: UpdateFollowUpRequest,
    service: FollowUpService = Depends(get_follow_up_service),
):
    data = body.model_dump(exclude_unset=True)
    return service.update(
        follow_up_id,
        scheduled_at=data.get("scheduled_at"),
        note=data.get("note"),
        completed=data.get("completed"),
    )


@router.delete("/follow-ups/{follow_up_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_follow_up(
    follow_up_id: str,
    service: FollowUpService = Depends(get_follow_up_service),
):
    service.delete(follow_up_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@router.post("/{application_id}/roadmap/generate", status_code=http_status.HTTP_202_ACCEPTED, response_model=GenerateResponse)
def generate_roadmap(
    application_id: str,
    application_repo: SQLAlchemyApplicationRepository = Depends(get_application_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    if not application_repo.get_by_id(application_id):
        raise NotFoundError(f"Application {application_id} not found")
    execution_id = _dispatch(exec_repo, ExecutionType.ROADMAP_GENERATION, application_id)
    return GenerateResponse(execution_id=execution_id, status="queued", artifact="roadmap")


@router.post("/{application_id}/documents/{document_type}/generate", status_code=http_status.HTTP_202_ACCEPTED, response_model=GenerateResponse)
def generate_document(
    application_id: str,
    document_type: str,
    application_repo: SQLAlchemyApplicationRepository = Depends(get_application_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    if document_type not in DocumentType.ALL:
        raise BadRequestError(
            f"Invalid document type '{document_type}'; allowed: {', '.join(DocumentType.ALL)}"
        )
    if not application_repo.get_by_id(application_id):
        raise NotFoundError(f"Application {application_id} not found")
    execution_id = _dispatch(exec_repo, _EXECUTION_TYPE_BY_DOCUMENT[document_type], application_id)
    return GenerateResponse(execution_id=execution_id, status="queued", artifact=document_type)


@router.patch("/documents/{document_id}", response_model=ApplicationDocumentSchema)
def update_document(
    document_id: str,
    body: UpdateDocumentRequest,
    service: DocumentService = Depends(get_document_service),
):
    return service.update_content(document_id, body.content)


@router.delete("/documents/{document_id}", status_code=http_status.HTTP_200_OK, response_model=DeleteResponse)
def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    service.delete(document_id)
    return DeleteResponse(status="deleted")
