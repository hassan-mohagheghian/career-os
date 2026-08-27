from __future__ import annotations

import json
from typing import Any
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from processing.domain.entities.processing_execution import ProcessingExecution
from processing.domain.repositories.processing_execution_repository import (
    IProcessingExecutionRepository,
)
from processing.infrastructure.models.processing_execution_model import (
    ProcessingExecutionModel,
)


def _ts(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def model_to_dict(model: ProcessingExecutionModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "execution_type": model.execution_type,
        "status": model.status,
        "target_type": model.target_type,
        "target_id": model.target_id,
        "created_at": _ts(model.created_at),
        "started_at": _ts(model.started_at),
        "finished_at": _ts(model.finished_at),
        "retry_count": model.retry_count,
        "error_message": model.error_message,
        "workflow_progress": _loads(model.workflow_progress),
        "heartbeat_at": _ts(model.heartbeat_at),
    }


def _loads(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def _dumps(value: dict[str, Any] | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value, default=str)


class SQLAlchemyProcessingExecutionRepository(IProcessingExecutionRepository):
    def __init__(self, session: Session):
        self._session = session

    def save(self, execution: ProcessingExecution) -> ProcessingExecution:
        model = (
            self._session.query(ProcessingExecutionModel)
            .filter(ProcessingExecutionModel.id == execution.id)
            .first()
        )

        if model:
            model.status = execution.status.value
            model.started_at = execution.started_at
            model.finished_at = execution.finished_at
            model.retry_count = execution.retry_count
            model.error_message = execution.error_message
            model.workflow_progress = _dumps(execution.workflow_progress)
            model.heartbeat_at = execution.heartbeat_at
        else:
            model = ProcessingExecutionModel(
                id=execution.id,
                execution_type=execution.execution_type.value,
                status=execution.status.value,
                target_type=execution.target_type,
                target_id=execution.target_id,
                created_at=execution.created_at,
                started_at=execution.started_at,
                finished_at=execution.finished_at,
                retry_count=execution.retry_count,
                error_message=execution.error_message,
                workflow_progress=_dumps(execution.workflow_progress),
                heartbeat_at=execution.heartbeat_at,
            )
            self._session.add(model)

        self._session.commit()
        self._session.refresh(model)
        return ProcessingExecution.from_dict(model_to_dict(model))

    def get_by_id(self, execution_id: str) -> ProcessingExecution | None:
        model = (
            self._session.query(ProcessingExecutionModel)
            .filter(ProcessingExecutionModel.id == execution_id)
            .first()
        )
        if not model:
            return None
        return ProcessingExecution.from_dict(model_to_dict(model))

    def list_by_target(
        self, target_type: str, target_id: str
    ) -> list[ProcessingExecution]:
        models = (
            self._session.query(ProcessingExecutionModel)
            .filter(
                ProcessingExecutionModel.target_type == target_type,
                ProcessingExecutionModel.target_id == target_id,
            )
            .order_by(ProcessingExecutionModel.created_at.desc())
            .all()
        )
        return [ProcessingExecution.from_dict(model_to_dict(m)) for m in models]

    _ACTIVE_STATUSES = ("queued", "starting", "running", "failed")

    def active_execution(
        self, target_type: str, target_id: str
    ) -> ProcessingExecution | None:
        model = (
            self._session.query(ProcessingExecutionModel)
            .filter(
                ProcessingExecutionModel.target_type == target_type,
                ProcessingExecutionModel.target_id == target_id,
                ProcessingExecutionModel.status.in_(self._ACTIVE_STATUSES),
            )
            .order_by(
                ProcessingExecutionModel.created_at.desc(),
                ProcessingExecutionModel.id.desc(),
            )
            .first()
        )
        if not model:
            return None
        return ProcessingExecution.from_dict(model_to_dict(model))

    def latest_by_target_ids(
        self, target_type: str, target_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Return the most recent execution per target id (batch, no N+1).

        Returns ``{target_id: execution_dict}`` for targets that have at least
        one execution. Used by the jobs list projection so each row carries the
        real persisted execution (status, id, timestamps).
        """
        if not target_ids:
            return {}
        models = (
            self._session.query(ProcessingExecutionModel)
            .filter(
                ProcessingExecutionModel.target_type == target_type,
                ProcessingExecutionModel.target_id.in_(target_ids),
            )
            .order_by(
                ProcessingExecutionModel.target_id.asc(),
                ProcessingExecutionModel.created_at.desc(),
                ProcessingExecutionModel.id.desc(),
            )
            .all()
        )
        latest: dict[str, dict[str, Any]] = {}
        for model in models:
            latest.setdefault(model.target_id, model_to_dict(model))
        return latest

    def target_ids_with_status(self, target_type: str, status: str) -> set[str]:
        """Return target ids whose latest execution has the given status.

        Delegates to :meth:`latest_statuses` so "latest" keeps a single
        definition across the repository.
        """
        return {
            target_id
            for target_id, target_status in self.latest_statuses(target_type).items()
            if target_status == status
        }

    def latest_statuses(self, target_type: str) -> dict[str, str]:
        """Return ``{target_id: latest_status}`` for every target of the type.

        Uses a window function (ROW_NUMBER over ``created_at desc`` partitioned
        by ``target_id``) so only the most recent execution per target counts.
        ``id desc`` breaks ties between executions sharing the same timestamp.
        """
        row_number = func.row_number().over(
            partition_by=ProcessingExecutionModel.target_id,
            order_by=(
                ProcessingExecutionModel.created_at.desc(),
                ProcessingExecutionModel.id.desc(),
            ),
        )
        ranked = (
            select(
                ProcessingExecutionModel.target_id.label("target_id"),
                ProcessingExecutionModel.status.label("status"),
                row_number.label("rn"),
            )
            .where(ProcessingExecutionModel.target_type == target_type)
            .subquery()
        )
        rows = (
            self._session.query(ranked.c.target_id, ranked.c.status)
            .filter(ranked.c.rn == 1)
            .all()
        )
        return {row.target_id: row.status for row in rows}

    def target_ids(self, target_type: str) -> set[str]:
        """Return distinct target ids that have at least one execution."""
        rows = (
            self._session.query(ProcessingExecutionModel.target_id)
            .filter(ProcessingExecutionModel.target_type == target_type)
            .distinct()
            .all()
        )
        return {row[0] for row in rows}

    def delete_by_target(self, target_type: str, target_id: str) -> int:
        return (
            self._session.query(ProcessingExecutionModel)
            .filter(
                ProcessingExecutionModel.target_type == target_type,
                ProcessingExecutionModel.target_id == target_id,
            )
            .delete(synchronize_session=False)
        )

    def list_recent(self, limit: int = 50) -> list[ProcessingExecution]:
        models = (
            self._session.query(ProcessingExecutionModel)
            .order_by(ProcessingExecutionModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [ProcessingExecution.from_dict(model_to_dict(m)) for m in models]

    def update_status(self, execution_id: str, status: str, **extra: Any) -> bool:
        model = (
            self._session.query(ProcessingExecutionModel)
            .filter(ProcessingExecutionModel.id == execution_id)
            .first()
        )
        if not model:
            return False
        model.status = status
        for key, value in extra.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self._session.commit()
        return True

    def stale_queued_executions(
        self, older_than_seconds: int = 60
    ) -> list[ProcessingExecution]:
        from datetime import datetime, timedelta, UTC

        cutoff = (datetime.now(UTC) - timedelta(seconds=older_than_seconds)).isoformat()
        models = (
            self._session.query(ProcessingExecutionModel)
            .filter(
                ProcessingExecutionModel.status == "queued",
                ProcessingExecutionModel.created_at < cutoff,
            )
            .order_by(ProcessingExecutionModel.created_at.asc())
            .all()
        )
        return [ProcessingExecution.from_dict(model_to_dict(m)) for m in models]

    def stale_running_executions(
        self, older_than_seconds: int = 600
    ) -> list[ProcessingExecution]:
        """Return RUNNING executions whose worker has likely crashed.

        An execution is considered stale when:
        - heartbeat_at is set and older than ``older_than_seconds`` (worker
          stopped sending heartbeats), OR
        - heartbeat_at is NULL and started_at is older than
          ``older_than_seconds`` (legacy rows without heartbeat support).
        """
        from datetime import datetime, timedelta, UTC

        cutoff = (datetime.now(UTC) - timedelta(seconds=older_than_seconds)).isoformat()
        models = (
            self._session.query(ProcessingExecutionModel)
            .filter(
                ProcessingExecutionModel.status == "running",
                (
                    (
                        ProcessingExecutionModel.heartbeat_at.isnot(None)
                        & (ProcessingExecutionModel.heartbeat_at < cutoff)
                    )
                    | (
                        ProcessingExecutionModel.heartbeat_at.is_(None)
                        & ProcessingExecutionModel.started_at.isnot(None)
                        & (ProcessingExecutionModel.started_at < cutoff)
                    )
                ),
            )
            .order_by(ProcessingExecutionModel.started_at.asc())
            .all()
        )
        return [ProcessingExecution.from_dict(model_to_dict(m)) for m in models]
