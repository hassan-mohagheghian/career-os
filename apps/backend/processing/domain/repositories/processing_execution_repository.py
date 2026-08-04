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
    def latest_by_target_ids(
        self, target_type: str, target_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Return the most recent execution per target id (batch, no N+1)."""
        ...

    @abstractmethod
    def target_ids_with_status(self, target_type: str, status: str) -> set[str]:
        """Return target ids whose latest execution has the given status."""
        ...

    @abstractmethod
    def delete_by_target(self, target_type: str, target_id: str) -> int:
        """Delete all executions for a target. Returns number deleted."""
        ...

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list[ProcessingExecution]:
        ...

    @abstractmethod
    def update_status(self, execution_id: str, status: str, **extra: Any) -> bool:
        ...
