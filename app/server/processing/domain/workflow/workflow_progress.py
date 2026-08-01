"""WorkflowProgress — the user-facing representation of a processing run.

It is the stable contract between the backend execution runtime, the LangGraph
workflow engine, ProcessingExecution, and the frontend workflow visualization.

See docs/domain/processing/workflow-progress.md.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from processing.domain.workflow.workflow_step import WorkflowStep


class WorkflowProgressStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowProgress(BaseModel):
    id: str
    name: str = "Job Context Preparation"
    status: WorkflowProgressStatus = WorkflowProgressStatus.PENDING
    current_step: WorkflowStep | None = None
    progress: float | None = None
    steps: list[WorkflowStep] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowProgress":
        return cls.model_validate(data)
