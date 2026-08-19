"""SQLAlchemy implementation of the status-event (timeline) repository."""

from typing import Any

from sqlalchemy.orm import Session

from applications.domain.repositories.status_event_repository import IStatusEventRepository
from applications.infrastructure.mappers import (
    dict_to_status_event_model,
    status_event_model_to_dict,
)
from applications.infrastructure.models.application_model import ApplicationStatusEventModel


class SQLAlchemyStatusEventRepository(IStatusEventRepository):
    """SQLAlchemy implementation of the status-event repository."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_status_event_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return status_event_model_to_dict(model)

    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(ApplicationStatusEventModel)
            .filter(ApplicationStatusEventModel.application_id == application_id)
            .order_by(ApplicationStatusEventModel.changed_at.asc())
            .all()
        )
        return [status_event_model_to_dict(r) for r in rows]

    def get_by_id(self, event_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationStatusEventModel)
            .filter(ApplicationStatusEventModel.id == event_id)
            .first()
        )
        return status_event_model_to_dict(model) if model else None

    def update(self, event_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationStatusEventModel)
            .filter(ApplicationStatusEventModel.id == event_id)
            .first()
        )
        if not model:
            return None
        for field in ("changed_at", "updated_at"):
            if field in data:
                setattr(model, field, data[field])
        self._session.commit()
        return status_event_model_to_dict(model)

    def delete(self, event_id: str) -> bool:
        deleted = (
            self._session.query(ApplicationStatusEventModel)
            .filter(ApplicationStatusEventModel.id == event_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)