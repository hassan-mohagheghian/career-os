"""JobProcessingState — the strongly typed LangGraph state.

This state flows through the JobContextPreparationGraph nodes:

    execution_id
    job_id
    job
    sources
    fetched_contents
    extracted_contents
    notes
    processing_context
    validation_result
    errors
    status

The state is Pydantic-based and type-safe. Nodes receive and return the
full state model.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.job_data import JobData
from processing.domain.workflow.job_processing_context import JobProcessingContext
from processing.domain.workflow.source import JobSource
from processing.domain.workflow.validation_result import ContextValidationResult
from processing.domain.workflow.workflow_progress import WorkflowProgress


class JobProcessingState(BaseModel):
    execution_id: str
    job_id: str
    job: JobData | None = None
    sources: list[JobSource] = Field(default_factory=list)
    fetched_contents: list[FetchedContent] = Field(default_factory=list)
    extracted_contents: list[ExtractedContent] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    processing_context: JobProcessingContext | None = None
    validation_result: ContextValidationResult | None = None
    errors: list[str] = Field(default_factory=list)
    workflow_progress: WorkflowProgress | None = None
    status: ExecutionStatus = ExecutionStatus.CREATED
    analysis_context: dict[str, Any] = Field(default_factory=dict)
    analysis_result: dict[str, Any] | None = None
    persisted: bool = False
