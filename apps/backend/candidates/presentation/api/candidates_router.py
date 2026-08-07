"""Candidate API router — reads the canonical profile, sources and versions.

The Candidate Profile is built by the candidate processing workflow (Phase 101)
and read here. ``POST /analyze`` triggers a new candidate processing run via the
processing pipeline, mirroring the job/company process endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status as http_status

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
from shared.application.exceptions import NotFoundError

from candidates.presentation.api.schemas.candidates import (
    CandidateAnalyzeResponse,
    CandidateProfileResponse,
    CandidateSourceListResponse,
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
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
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
