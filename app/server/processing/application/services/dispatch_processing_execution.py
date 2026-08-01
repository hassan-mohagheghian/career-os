"""Application service for dispatching a ProcessingExecution to the queue.

Responsible for the flow:

    Create ProcessingExecution
        ↓
    Mark execution queued
        ↓
    Dispatch TaskIQ task
        ↓
    Publish ExecutionQueued event

The domain layer stays independent from TaskIQ — dispatch is an
infrastructure concern coordinated by this application service.
"""

from __future__ import annotations

from processing.domain.enums import ExecutionStatus
from processing.domain.entities.processing_execution import ProcessingExecution
from processing.domain.repositories.processing_execution_repository import IProcessingExecutionRepository
from shared.application.exceptions import NotFoundError, ConflictError


class DispatchProcessingExecutionService:
    def __init__(self, repository: IProcessingExecutionRepository):
        self._repository = repository

    def dispatch(self, execution_id: str) -> bool:
        execution = self._repository.get_by_id(execution_id)
        if not execution:
            raise NotFoundError(f"ProcessingExecution {execution_id} not found")
        if execution.status != ExecutionStatus.CREATED:
            raise ConflictError(
                f"ProcessingExecution {execution_id} already dispatched "
                f"(status={execution.status.value})"
            )

        execution.status = ExecutionStatus.QUEUED
        self._repository.save(execution)

        job_id = self._job_id(execution)

        from shared.infrastructure.taskiq.client import enqueue_execution_sync
        from shared.infrastructure.events.processing_events import (
            publish_sync,
            EXECUTION_QUEUED,
        )

        enqueue_execution_sync(execution_id)
        publish_sync(
            EXECUTION_QUEUED,
            execution.id,
            job_id,
            ExecutionStatus.QUEUED.value,
        )
        return True

    @staticmethod
    def _job_id(execution: ProcessingExecution) -> str | None:
        if execution.target_type == "job":
            return execution.target_id
        return None
