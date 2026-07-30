from __future__ import annotations

from typing import Any
from datetime import datetime

from sqlalchemy.orm import Session

from processing.domain.entities.processing_execution import ProcessingExecution
from processing.domain.repositories.processing_execution_repository import IProcessingExecutionRepository
from processing.infrastructure.models.processing_execution_model import ProcessingExecutionModel


def model_to_dict(model: ProcessingExecutionModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "execution_type": model.execution_type,
        "status": model.status,
        "target_type": model.target_type,
        "target_id": model.target_id,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "started_at": model.started_at.isoformat() if model.started_at else None,
        "finished_at": model.finished_at.isoformat() if model.finished_at else None,
        "retry_count": model.retry_count,
        "error_message": model.error_message,
    }


class SQLAlchemyProcessingExecutionRepository(IProcessingExecutionRepository):
    def __init__(self, session: Session):
        self._session = session

    def save(self, execution: ProcessingExecution) -> ProcessingExecution:
        model = self._session.query(ProcessingExecutionModel).filter(
            ProcessingExecutionModel.id == execution.id
        ).first()

        if model:
            model.status = execution.status.value
            model.started_at = execution.started_at
            model.finished_at = execution.finished_at
            model.retry_count = execution.retry_count
            model.error_message = execution.error_message
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
            )
            self._session.add(model)

        self._session.commit()
        self._session.refresh(model)
        return ProcessingExecution.from_dict(model_to_dict(model))

    def get_by_id(self, execution_id: str) -> ProcessingExecution | None:
        model = self._session.query(ProcessingExecutionModel).filter(
            ProcessingExecutionModel.id == execution_id
        ).first()
        if not model:
            return None
        return ProcessingExecution.from_dict(model_to_dict(model))

    def list_by_target(self, target_type: str, target_id: str) -> list[ProcessingExecution]:
        models = self._session.query(ProcessingExecutionModel).filter(
            ProcessingExecutionModel.target_type == target_type,
            ProcessingExecutionModel.target_id == target_id,
        ).order_by(ProcessingExecutionModel.created_at.desc()).all()
        return [ProcessingExecution.from_dict(model_to_dict(m)) for m in models]

    def update_status(self, execution_id: str, status: str, **extra: Any) -> bool:
        model = self._session.query(ProcessingExecutionModel).filter(
            ProcessingExecutionModel.id == execution_id
        ).first()
        if not model:
            return False
        model.status = status
        for key, value in extra.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self._session.commit()
        return True
