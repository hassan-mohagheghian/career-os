"""SQLAlchemy implementation of the application repository."""

from typing import Any

from sqlalchemy.orm import Session

from applications.domain.repositories.application_repository import IApplicationRepository
from applications.infrastructure.mappers import (
    application_model_to_dict,
    dict_to_application_model,
)
from applications.infrastructure.models.application_model import (
    ApplicationDocumentModel,
    ApplicationFollowUpModel,
    ApplicationModel,
    ApplicationStatusEventModel,
)


class SQLAlchemyApplicationRepository(IApplicationRepository):
    """SQLAlchemy implementation of the application repository."""

    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, application_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationModel)
            .filter(ApplicationModel.id == application_id)
            .first()
        )
        return application_model_to_dict(model) if model else None

    def get_by_job_id(self, job_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationModel)
            .filter(ApplicationModel.job_id == job_id)
            .first()
        )
        return application_model_to_dict(model) if model else None

    def list_ids_by_job(self, job_id: str) -> list[str]:
        return [
            row[0]
            for row in self._session.query(ApplicationModel.id)
            .filter(ApplicationModel.job_id == job_id)
            .all()
        ]

    def statuses_by_job_ids(self, job_ids: list[str]) -> dict[str, str]:
        if not job_ids:
            return {}
        rows = (
            self._session.query(ApplicationModel.job_id, ApplicationModel.status)
            .filter(ApplicationModel.job_id.in_(job_ids))
            .all()
        )
        return {job_id: status for job_id, status in rows}

    def job_ids_with_application(self) -> list[str]:
        return [
            row[0]
            for row in self._session.query(ApplicationModel.job_id).distinct().all()
        ]

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_application_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return application_model_to_dict(model)

    def update(self, application_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationModel)
            .filter(ApplicationModel.id == application_id)
            .first()
        )
        if not model:
            return None
        for field in ("status", "applied_at", "updated_at"):
            if field in data:
                setattr(model, field, data[field])
        self._session.commit()
        return application_model_to_dict(model)

    def delete_by_job(self, job_id: str) -> int:
        app_ids = self.list_ids_by_job(job_id)
        if not app_ids:
            return 0
        for child_model in (ApplicationFollowUpModel, ApplicationDocumentModel, ApplicationStatusEventModel):
            self._session.query(child_model).filter(
                child_model.application_id.in_(app_ids)
            ).delete(synchronize_session=False)
        deleted = self._session.query(ApplicationModel).filter(
            ApplicationModel.job_id == job_id
        ).delete(synchronize_session=False)
        self._session.commit()
        return int(deleted)
