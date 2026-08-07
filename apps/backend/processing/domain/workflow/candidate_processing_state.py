"""CandidateProcessingState — the strongly typed LangGraph state for the
candidate processing workflow.

This state flows through the CandidateSourcePreparationGraph and then the
CandidateProcessingGraph nodes:

    execution_id
    profile_id
    profile
    pending_sources
    extracted_sources
    merge_result
    errors
    status

The state is Pydantic-based and type-safe. Nodes receive and return the full
state model. Reuses the shared WorkflowProgress value object; the runner
persists the final progress tree onto the ProcessingExecution record.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.workflow_progress import WorkflowProgress


class CandidateProcessingState(BaseModel):
    execution_id: str
    profile_id: str = ""
    profile: dict[str, Any] | None = None
    pending_sources: list[dict[str, Any]] = Field(default_factory=list)
    extracted_sources: list[dict[str, Any]] = Field(default_factory=list)
    merge_result: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)
    workflow_progress: WorkflowProgress | None = None
    status: ExecutionStatus = ExecutionStatus.CREATED
