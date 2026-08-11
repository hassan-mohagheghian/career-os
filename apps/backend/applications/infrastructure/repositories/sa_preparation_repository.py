"""SQLAlchemy implementation of the preparation repository."""

from typing import Any

from sqlalchemy.orm import Session

from applications.domain.repositories.preparation_repository import IPreparationRepository
from applications.infrastructure.mappers import (
    dict_to_preparation_model,
    preparation_model_to_dict,
)
from applications.infrastructure.models.application_model import ApplicationPreparationModel


class SQLAlchemyPreparationRepository(IPreparationRepository):
    """SQLAlchemy implementation of the preparation repository."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_preparation_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return preparation_model_to_dict(model)

    def get_latest(self, application_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationPreparationModel)
            .filter(ApplicationPreparationModel.application_id == application_id)
            .order_by(ApplicationPreparationModel.version.desc())
            .first()
        )
        return preparation_model_to_dict(model) if model else None

    def get_next_version(self, application_id: str) -> int:
        latest = self.get_latest(application_id)
        return int(latest["version"]) + 1 if latest else 1
