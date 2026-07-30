from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from processing.domain.entities.processing_execution import ProcessingExecution


class IProcessingExecutionRepository(ABC):
    @abstractmethod
    def save(self, execution: ProcessingExecution) -> ProcessingExecution:
        ...

    @abstractmethod
    def get_by_id(self, execution_id: str) -> ProcessingExecution | None:
        ...

    @abstractmethod
    def list_by_target(self, target_type: str, target_id: str) -> list[ProcessingExecution]:
        ...

    @abstractmethod
    def update_status(self, execution_id: str, status: str, **extra: Any) -> bool:
        ...
