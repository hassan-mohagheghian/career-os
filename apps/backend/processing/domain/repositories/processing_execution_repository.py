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
    def active_execution(self, target_type: str, target_id: str) -> ProcessingExecution | None:
        """Return the most recent active execution for a target, if any.

        Active means the execution is still in flight or awaiting action:
        ``queued``, ``starting``, ``running`` or ``failed``. Used to enforce the
        single-active-execution-per-target invariant.
        """
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
    def latest_statuses(self, target_type: str) -> dict[str, str]:
        """Return ``{target_id: latest_status}`` for every target of the type.

        Used by the jobs list to sort rows by the same execution status that
        is displayed in each row.
        """
        ...

    @abstractmethod
    def target_ids(self, target_type: str) -> set[str]:
        """Return distinct target ids that have at least one execution."""
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
