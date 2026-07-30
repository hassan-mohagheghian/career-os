from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any

from shared.domain.entity import BaseEntity
from processing.domain.enums import ExecutionType, ExecutionStatus


class ProcessingExecution(BaseEntity):
    def __init__(
        self,
        execution_type: ExecutionType,
        target_type: str,
        target_id: str,
        id: str | None = None,
        status: ExecutionStatus = ExecutionStatus.CREATED,
        created_at: datetime | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        retry_count: int = 0,
        error_message: str | None = None,
    ):
        if id is None:
            id = str(uuid.uuid4())
        super().__init__(id=id, created_at=created_at, updated_at=created_at)
        self.execution_type = execution_type
        self.target_type = target_type
        self.target_id = target_id
        self._status = status
        self._started_at = started_at
        self._finished_at = finished_at
        self._retry_count = retry_count
        self._error_message = error_message

    @property
    def status(self) -> ExecutionStatus:
        return self._status

    @status.setter
    def status(self, value: ExecutionStatus) -> None:
        self._status = value
        self._updated_at = datetime.now(UTC)

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @started_at.setter
    def started_at(self, value: datetime | None) -> None:
        self._started_at = value

    @property
    def finished_at(self) -> datetime | None:
        return self._finished_at

    @finished_at.setter
    def finished_at(self, value: datetime | None) -> None:
        self._finished_at = value

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @retry_count.setter
    def retry_count(self, value: int) -> None:
        self._retry_count = value

    @property
    def error_message(self) -> str | None:
        return self._error_message

    @error_message.setter
    def error_message(self, value: str | None) -> None:
        self._error_message = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "execution_type": self.execution_type.value,
            "status": self._status.value,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "created_at": self._created_at.isoformat() if self._created_at else None,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "finished_at": self._finished_at.isoformat() if self._finished_at else None,
            "retry_count": self._retry_count,
            "error_message": self._error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessingExecution:
        return cls(
            id=data.get("id"),
            execution_type=ExecutionType(data["execution_type"]),
            target_type=data["target_type"],
            target_id=str(data["target_id"]),
            status=ExecutionStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            finished_at=datetime.fromisoformat(data["finished_at"]) if data.get("finished_at") else None,
            retry_count=data.get("retry_count", 0),
            error_message=data.get("error_message"),
        )
