"""RoadmapGenerationState — the workflow state for AI roadmap generation.

The state flows through the RoadmapGenerationGraph nodes:

    execution_id
    application_id
    job_id
    intent            (ExecutionType.ROADMAP_GENERATION)
    context           (job, analysis, company, intelligence, candidate_profile)
    result            (schema-valid generation payload)
    persisted_roadmap_id (roadmap row id)
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


class RoadmapGenerationState(BaseModel):
    execution_id: str
    application_id: str
    job_id: str
    intent: str = "roadmap_generation"
    context: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    persisted_roadmap_id: str | None = None
    errors: list[str] = Field(default_factory=list)
    workflow_progress: WorkflowProgress | None = None
    status: ExecutionStatus = ExecutionStatus.CREATED