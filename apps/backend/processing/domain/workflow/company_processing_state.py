"""CompanyProcessingState — the strongly typed LangGraph state for the
company processing workflow.

This state flows through the CompanyContextPreparationGraph and then the
CompanyAnalysisGraph nodes:

    execution_id
    company_id
    company
    sources
    fetched_contents
    extracted_contents
    notes
    processing_context
    validation_result
    errors
    status

The state is Pydantic-based and type-safe. Nodes receive and return the full
state model. Reuses the shared FetchedContent / ExtractedContent /
ContextValidationResult / WorkflowProgress value objects.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_data import CompanyData
from processing.domain.workflow.company_processing_context import CompanyProcessingContext
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.source import JobSource
from processing.domain.workflow.validation_result import ContextValidationResult
from processing.domain.workflow.workflow_progress import WorkflowProgress


class CompanyProcessingState(BaseModel):
    execution_id: str
    company_id: str
    company: CompanyData | None = None
    sources: list[JobSource] = Field(default_factory=list)
    fetched_contents: list[FetchedContent] = Field(default_factory=list)
    extracted_contents: list[ExtractedContent] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    processing_context: CompanyProcessingContext | None = None
    validation_result: ContextValidationResult | None = None
    errors: list[str] = Field(default_factory=list)
    workflow_progress: WorkflowProgress | None = None
    status: ExecutionStatus = ExecutionStatus.CREATED
    analysis_context: dict[str, Any] = Field(default_factory=dict)
    analysis_result: dict[str, Any] | None = None
    persisted: bool = False
