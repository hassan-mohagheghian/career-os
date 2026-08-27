"""Candidate API router — reads the canonical profile, sources and versions.

The Candidate Profile is built by the candidate processing workflow (Phase 101)
and read here. ``POST /analyze`` triggers a new candidate processing run via the
processing pipeline, mirroring the job/company process endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status as http_status
from fastapi.responses import JSONResponse

from candidates.infrastructure import (
    SQLAlchemyCandidateProfileRepository,
    SQLAlchemyCandidateSourceRepository,
)
from processing.domain.enums import ExecutionType, ExecutionStatus
from processing.application.use_cases.create_processing_execution import (
    CreateProcessingExecutionRequest,
    CreateProcessingExecutionUseCase,
)
from processing.application.services.dispatch_processing_execution import (
    DispatchProcessingExecutionService,
)
from processing.infrastructure import SQLAlchemyProcessingExecutionRepository
from dependencies import (
    get_candidate_profile_repo,
    get_candidate_source_repo,
    get_processing_execution_repo,
)
from shared.application.exceptions import BadRequestError, NotFoundError

from candidates.application.services.candidate_source_upload_service import (
    SUPPORTED_SOURCE_TYPES,
    CandidateSourceUploadService,
)
from candidates.presentation.api.schemas.candidates import (
    CandidateAnalyzeResponse,
    CandidateProfileResponse,
    CandidateSourceListResponse,
    CandidateSourceUploadRequest,
    CandidateSourceUploadResponse,
    CandidateVersionListResponse,
)

router = APIRouter()


@router.get("/profile", response_model=CandidateProfileResponse)
def get_profile(
    profile_repo: SQLAlchemyCandidateProfileRepository = Depends(get_candidate_profile_repo),
):
    profile = profile_repo.get_current_profile()
    if not profile:
        raise NotFoundError("No candidate profile found — run profile analysis first")
    return profile


@router.get("/sources", response_model=CandidateSourceListResponse)
def list_sources(
    profile_repo: SQLAlchemyCandidateProfileRepository = Depends(get_candidate_profile_repo),
    source_repo: SQLAlchemyCandidateSourceRepository = Depends(get_candidate_source_repo),
):
    profile = profile_repo.get_current_profile()
    if not profile:
        return CandidateSourceListResponse(items=[])
    return CandidateSourceListResponse(items=source_repo.list_for_profile(profile["id"]))


@router.post("/sources", status_code=http_status.HTTP_201_CREATED, response_model=CandidateSourceUploadResponse)
def upload_source(
    body: CandidateSourceUploadRequest,
    profile_repo: SQLAlchemyCandidateProfileRepository = Depends(get_candidate_profile_repo),
    source_repo: SQLAlchemyCandidateSourceRepository = Depends(get_candidate_source_repo),
):
    """Store raw profile text (resume / LinkedIn) as the next candidate source version.

    PII is masked on save and the source is left ``pending`` so the next
    candidate processing run extracts and marks it ``processed``.
    """
    if body.source_type not in SUPPORTED_SOURCE_TYPES:
        raise BadRequestError(
            f"Unsupported source type '{body.source_type}'; supported: {', '.join(SUPPORTED_SOURCE_TYPES)}"
        )
    if not body.raw_text.strip():
        raise BadRequestError("raw_text must not be empty")

    service = CandidateSourceUploadService(profile_repo, source_repo)
    stored = service.upload(body.source_type, body.raw_text)
    return CandidateSourceUploadResponse(
        id=stored["id"],
        source_type=stored["source_type"],
        version=stored["version"],
        status=stored["status"],
        raw_text=stored.get("raw_text", ""),
    )


@router.get("/versions", response_model=CandidateVersionListResponse)
def list_versions(
    profile_repo: SQLAlchemyCandidateProfileRepository = Depends(get_candidate_profile_repo),
):
    profile = profile_repo.get_current_profile()
    if not profile:
        return CandidateVersionListResponse(items=[])
    return CandidateVersionListResponse(items=profile_repo.list_versions(profile["id"]))


@router.post("/analyze", status_code=http_status.HTTP_202_ACCEPTED, response_model=CandidateAnalyzeResponse)
def analyze_profile(
    profile_repo: SQLAlchemyCandidateProfileRepository = Depends(get_candidate_profile_repo),
    source_repo: SQLAlchemyCandidateSourceRepository = Depends(get_candidate_source_repo),
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    profile = profile_repo.get_current_profile()
    if profile is None:
        return JSONResponse(
            status_code=http_status.HTTP_200_OK,
            content=CandidateAnalyzeResponse(status="noop", reason="no_profile").model_dump(),
        )
    if not source_repo.has_any_sources(profile["id"]):
        return JSONResponse(
            status_code=http_status.HTTP_200_OK,
            content=CandidateAnalyzeResponse(status="noop", reason="no_sources").model_dump(),
        )
    use_case = CreateProcessingExecutionUseCase(exec_repo)
    request = CreateProcessingExecutionRequest(
        execution_type=ExecutionType.CANDIDATE_PROCESSING,
        target_type="candidate",
        target_id="candidate",
    )
    response = use_case.execute(request)
    DispatchProcessingExecutionService(exec_repo).dispatch(response.execution_id)
    return CandidateAnalyzeResponse(
        execution_id=response.execution_id,
        status=ExecutionStatus.QUEUED.value,
    )
