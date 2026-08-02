from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from processing.domain.enums import ExecutionType, ExecutionStatus
from processing.domain.entities.processing_execution import ProcessingExecution
from processing.domain.repositories.processing_execution_repository import IProcessingExecutionRepository


@dataclass
class CreateProcessingExecutionRequest:
    execution_type: ExecutionType
    target_type: str
    target_id: str


@dataclass
class CreateProcessingExecutionResponse:
    execution_id: str
    status: ExecutionStatus


class CreateProcessingExecutionUseCase:
    def __init__(self, repository: IProcessingExecutionRepository):
        self._repository = repository

    def execute(self, request: CreateProcessingExecutionRequest) -> CreateProcessingExecutionResponse:
        execution = ProcessingExecution(
            execution_type=request.execution_type,
            target_type=request.target_type,
            target_id=request.target_id,
        )
        saved = self._repository.save(execution)
        return CreateProcessingExecutionResponse(
            execution_id=str(saved.id),
            status=saved.status,
        )
