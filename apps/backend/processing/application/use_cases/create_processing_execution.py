from __future__ import annotations

from dataclasses import dataclass

from processing.domain.enums import ExecutionType, ExecutionStatus
from processing.domain.entities.processing_execution import ProcessingExecution
from processing.domain.repositories.processing_execution_repository import (
    IProcessingExecutionRepository,
)
from shared.application.exceptions import ConflictError
from shared.infrastructure.process.logging_config import get_logger

log = get_logger("processing.create_execution")


@dataclass
class CreateProcessingExecutionRequest:
    execution_type: ExecutionType
    target_type: str
    target_id: str
    user_id: str = ""


@dataclass
class CreateProcessingExecutionResponse:
    execution_id: str
    status: ExecutionStatus


class CreateProcessingExecutionUseCase:
    def __init__(self, repository: IProcessingExecutionRepository):
        self._repository = repository

    def execute(
        self, request: CreateProcessingExecutionRequest
    ) -> CreateProcessingExecutionResponse:
        active = self._repository.active_execution(
            request.target_type, request.target_id
        )
        if active:
            if active.status == ExecutionStatus.FAILED:
                log.info(
                    "processing.execution.auto_cancel_failed",
                    execution_id=active.id,
                    target_type=request.target_type,
                    target_id=request.target_id,
                )
                self._cancel(active)
            else:
                raise ConflictError(
                    f"{request.target_type.capitalize()} {request.target_id} already has an active "
                    f"execution (status={active.status.value})"
                )
        execution = ProcessingExecution(
            execution_type=request.execution_type,
            target_type=request.target_type,
            target_id=request.target_id,
            user_id=request.user_id,
        )
        saved = self._repository.save(execution)
        return CreateProcessingExecutionResponse(
            execution_id=str(saved.id),
            status=saved.status,
        )

    def _cancel(self, execution: ProcessingExecution) -> None:
        from datetime import datetime, UTC

        execution.status = ExecutionStatus.CANCELLED
        execution.finished_at = datetime.now(UTC)
        if execution.workflow_progress:
            execution.workflow_progress["status"] = "cancelled"
        self._repository.save(execution)
