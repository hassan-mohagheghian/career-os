"""GenerationSession entity — aggregate root for tracking AI workflow executions.

Every graph execution creates a GenerationSession that tracks:
- Session ID, workflow type, status, progress
- Associated entity (Job, Company, Resume, etc.)
- Errors and completion timestamps
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Optional

from shared.domain.entity import BaseEntity


class GenerationSession(BaseEntity):
    """Tracks an AI workflow execution session."""

    def __init__(
        self,
        id: str | None = None,
        workflow_type: str = "",
        status: str = "pending",
        current_stage: str = "",
        progress: float = 0.0,
        errors: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.workflow_type = workflow_type
        self.status = status
        self.current_stage = current_stage
        self.progress = progress
        self.errors = errors or []
        self.metadata = metadata or {}
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.started_at = started_at or datetime.now(UTC)
        self.completed_at = completed_at

    @property
    def is_running(self) -> bool:
        return self.status in ("pending", "processing")

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        return self.status == "failed"

    def start(self) -> None:
        self.status = "processing"
        self.started_at = datetime.now(UTC)

    def complete(self) -> None:
        self.status = "completed"
        self.progress = 1.0
        self.completed_at = datetime.now(UTC)

    def fail(self, error: str) -> None:
        self.status = "failed"
        self.errors.append(error)
        self.completed_at = datetime.now(UTC)

    def update_progress(self, stage: str, progress: float) -> None:
        self.current_stage = stage
        self.progress = progress

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "current_stage": self.current_stage,
            "progress": self.progress,
            "errors": self.errors,
            "metadata": self.metadata,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenerationSession:
        return cls(
            id=data.get("id"),
            workflow_type=data.get("workflow_type", ""),
            status=data.get("status", "pending"),
            current_stage=data.get("current_stage", ""),
            progress=data.get("progress", 0.0),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {}),
            entity_type=data.get("entity_type"),
            entity_id=data.get("entity_id"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
