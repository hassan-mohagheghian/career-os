"""WorkflowStep — the user-facing representation of one processing stage.

WorkflowStep is owned by the Processing domain. It bridges internal workflow
execution nodes and frontend workflow visualization. LangGraph node names are
never exposed to clients; only the mapped WorkflowStep tree is.

See docs/domain/processing/workflow-step.md.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStepError(BaseModel):
    code: str = "PROCESSING_ERROR"
    message: str = ""


class WorkflowStep(BaseModel):
    id: str
    node_id: str | None = None
    title: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    progress: float | None = None
    displayable: bool = True
    children: list["WorkflowStep"] = Field(default_factory=list)
    error: WorkflowStepError | None = None
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        return cls.model_validate(data)
