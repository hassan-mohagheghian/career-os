"""ApplicationIntelligenceState — the workflow state for application artifact
generation (preparation plan / tailored resume / cover letter).

The state flows through the ApplicationIntelligenceGraph nodes:

    execution_id
    application_id
    job_id
    intent            (ExecutionType: application_preparation | application_resume | application_cover_letter)
    context           (job, analysis, company, intelligence, candidate_profile)
    result            (schema-valid generation payload)
    persisted_id      (preparation / document row id)
    errors
    status

The state is Pydantic-based and type-safe. Nodes receive and return the full
state model.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.workflow_progress import WorkflowProgress


class ApplicationIntelligenceState(BaseModel):
    execution_id: str
    application_id: str
    job_id: str
    intent: str = "application_preparation"
    context: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    persisted_id: str | None = None
    errors: list[str] = Field(default_factory=list)
    workflow_progress: WorkflowProgress | None = None
    status: ExecutionStatus = ExecutionStatus.CREATED
