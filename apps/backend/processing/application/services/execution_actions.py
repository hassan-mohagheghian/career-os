"""Execution action services — start / cancel / retry / remove queue entry.

Each action enforces the ProcessingExecution state machine and publishes the
corresponding user-facing event:

- start   → execution.created (re-dispatches a queued execution)
- cancel  → execution.cancelled
- retry   → execution.created (via dispatch)
- remove  → queue.entry.removed (or execution.cancelled for queued entries)

See docs/api/processing/start-processing.md,
docs/api/processing/cancel-processing.md,
docs/api/processing/retry-processing.md,
docs/api/processing/remove-processing-queue-entry.md.
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from processing.domain.enums import ExecutionStatus, ExecutionType
from processing.domain.repositories.processing_execution_repository import IProcessingExecutionRepository
from processing.application.use_cases.create_processing_execution import (
    CreateProcessingExecutionRequest,
    CreateProcessingExecutionUseCase,
)
from processing.application.services.dispatch_processing_execution import DispatchProcessingExecutionService
from shared.application.exceptions import NotFoundError, ConflictError
from shared.infrastructure.events import processing_events


class ExecutionActionService:
    def __init__(self, repository: IProcessingExecutionRepository):
        self._repository = repository

    def start(self, execution_id: str) -> dict[str, Any]:
        """Re-dispatch a queued execution so a worker picks it up.

        The execution is already in the queue, so this nudges TaskIQ to run it
        immediately. Allowed for queued / starting executions only.
        """
        execution = self._repository.get_by_id(execution_id)
        if not execution:
            raise NotFoundError(f"ProcessingExecution {execution_id} not found")
        if execution.status not in (
            ExecutionStatus.QUEUED,
            ExecutionStatus.STARTING,
        ):
            raise ConflictError(
                f"Execution {execution_id} cannot be started (status={execution.status.value})"
            )

        from shared.infrastructure.taskiq.client import enqueue_execution_sync

        enqueue_execution_sync(execution_id)
        processing_events.publish_sync(
            processing_events.EXECUTION_STARTED,
            execution.id,
            self._job_id(execution),
            execution.status.value,
            target_type=execution.target_type,
            target_id=execution.target_id,
            updated_at=datetime.now(UTC).isoformat(),
        )
        return {
            "execution_id": execution.id,
            "job_id": self._job_id(execution),
            "status": execution.status.value,
            "started": True,
        }

    def cancel(self, execution_id: str) -> dict[str, Any]:
        execution = self._repository.get_by_id(execution_id)
        if not execution:
            raise NotFoundError(f"ProcessingExecution {execution_id} not found")
        if execution.status not in (
            ExecutionStatus.QUEUED,
            ExecutionStatus.STARTING,
            ExecutionStatus.RUNNING,
        ):
            raise ConflictError(f"Execution {execution_id} cannot be cancelled (status={execution.status.value})")

        cancelled_at = datetime.now(UTC)
        execution.status = ExecutionStatus.CANCELLED
        execution.finished_at = cancelled_at
        if execution.workflow_progress:
            execution.workflow_progress["status"] = "cancelled"
        self._repository.save(execution)

        processing_events.publish_sync(
            processing_events.EXECUTION_CANCELLED,
            execution.id,
            self._job_id(execution),
            ExecutionStatus.CANCELLED.value,
            target_type=execution.target_type,
            target_id=execution.target_id,
            updated_at=cancelled_at.isoformat(),
        )
        return {
            "execution_id": execution.id,
            "status": ExecutionStatus.CANCELLED.value,
            "cancelled_at": cancelled_at.isoformat(),
        }

    def retry(self, execution_id: str) -> dict[str, Any]:
        previous = self._repository.get_by_id(execution_id)
        if not previous:
            raise NotFoundError(f"ProcessingExecution {execution_id} not found")
        if previous.status != ExecutionStatus.FAILED:
            raise ConflictError(f"Only failed executions can be retried (status={previous.status.value})")

        use_case = CreateProcessingExecutionUseCase(self._repository)
        request = CreateProcessingExecutionRequest(
            execution_type=previous.execution_type,
            target_type=previous.target_type,
            target_id=previous.target_id,
        )
        created = use_case.execute(request)

        DispatchProcessingExecutionService(self._repository).dispatch(created.execution_id)

        return {
            "execution_id": created.execution_id,
            "job_id": previous.target_id,
            "status": ExecutionStatus.QUEUED.value,
            "retry_of": previous.id,
        }

    def remove_queue_entry(self, execution_id: str) -> dict[str, Any]:
        execution = self._repository.get_by_id(execution_id)
        if not execution:
            raise NotFoundError(f"ProcessingExecution {execution_id} not found")

        if execution.status == ExecutionStatus.QUEUED:
            cancelled_at = datetime.now(UTC)
            execution.status = ExecutionStatus.CANCELLED
            execution.finished_at = cancelled_at
            if execution.workflow_progress:
                execution.workflow_progress["status"] = "cancelled"
            self._repository.save(execution)
            processing_events.publish_sync(
                processing_events.EXECUTION_CANCELLED,
                execution.id,
                self._job_id(execution),
                ExecutionStatus.CANCELLED.value,
                target_type=execution.target_type,
                target_id=execution.target_id,
                updated_at=cancelled_at.isoformat(),
            )
        elif execution.status == ExecutionStatus.FAILED:
            cancelled_at = datetime.now(UTC)
            execution.status = ExecutionStatus.CANCELLED
            execution.finished_at = cancelled_at
            if execution.workflow_progress:
                execution.workflow_progress["status"] = "cancelled"
            self._repository.save(execution)
            processing_events.publish_sync(
                processing_events.QUEUE_ENTRY_REMOVED,
                execution.id,
                self._job_id(execution),
                ExecutionStatus.CANCELLED.value,
                target_type=execution.target_type,
                target_id=execution.target_id,
            )
        else:
            raise ConflictError(
                f"Execution {execution_id} cannot be removed (status={execution.status.value})"
            )

        return {"execution_id": execution.id, "removed": True}

    @staticmethod
    def _job_id(execution) -> str | None:
        if execution.target_type == "job":
            return execution.target_id
        return None
