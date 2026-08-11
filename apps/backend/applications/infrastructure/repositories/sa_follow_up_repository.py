"""SQLAlchemy implementation of the follow-up repository."""

from typing import Any

from sqlalchemy.orm import Session

from applications.domain.repositories.follow_up_repository import IFollowUpRepository
from applications.infrastructure.mappers import (
    dict_to_follow_up_model,
    follow_up_model_to_dict,
)
from applications.infrastructure.models.application_model import ApplicationFollowUpModel


class SQLAlchemyFollowUpRepository(IFollowUpRepository):
    """SQLAlchemy implementation of the follow-up repository."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_follow_up_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return follow_up_model_to_dict(model)

    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(ApplicationFollowUpModel)
            .filter(ApplicationFollowUpModel.application_id == application_id)
            .order_by(ApplicationFollowUpModel.scheduled_at.asc())
            .all()
        )
        return [follow_up_model_to_dict(r) for r in rows]

    def get_by_id(self, follow_up_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationFollowUpModel)
            .filter(ApplicationFollowUpModel.id == follow_up_id)
            .first()
        )
        return follow_up_model_to_dict(model) if model else None

    def update(self, follow_up_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationFollowUpModel)
            .filter(ApplicationFollowUpModel.id == follow_up_id)
            .first()
        )
        if not model:
            return None
        for field in ("scheduled_at", "note", "completed_at", "updated_at"):
            if field in data:
                setattr(model, field, data[field])
        self._session.commit()
        return follow_up_model_to_dict(model)

    def delete(self, follow_up_id: str) -> bool:
        deleted = (
            self._session.query(ApplicationFollowUpModel)
            .filter(ApplicationFollowUpModel.id == follow_up_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)
