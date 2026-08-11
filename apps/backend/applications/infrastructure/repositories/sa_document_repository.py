"""SQLAlchemy implementation of the document repository."""

from typing import Any

from sqlalchemy.orm import Session

from applications.domain.repositories.document_repository import IDocumentRepository
from applications.infrastructure.mappers import (
    dict_to_document_model,
    document_model_to_dict,
)
from applications.infrastructure.models.application_model import ApplicationDocumentModel


class SQLAlchemyDocumentRepository(IDocumentRepository):
    """SQLAlchemy implementation of the document repository."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_document_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return document_model_to_dict(model)

    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(ApplicationDocumentModel)
            .filter(ApplicationDocumentModel.application_id == application_id)
            .order_by(ApplicationDocumentModel.created_at.desc())
            .all()
        )
        return [document_model_to_dict(r) for r in rows]

    def list_by_type(self, application_id: str, document_type: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(ApplicationDocumentModel)
            .filter(
                ApplicationDocumentModel.application_id == application_id,
                ApplicationDocumentModel.document_type == document_type,
            )
            .order_by(ApplicationDocumentModel.version.desc())
            .all()
        )
        return [document_model_to_dict(r) for r in rows]

    def get_by_id(self, document_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationDocumentModel)
            .filter(ApplicationDocumentModel.id == document_id)
            .first()
        )
        return document_model_to_dict(model) if model else None

    def get_next_version(self, application_id: str, document_type: str) -> int:
        rows = self.list_by_type(application_id, document_type)
        return int(rows[0]["version"]) + 1 if rows else 1

    def update(self, document_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationDocumentModel)
            .filter(ApplicationDocumentModel.id == document_id)
            .first()
        )
        if not model:
            return None
        for field in ("content", "updated_at"):
            if field in data:
                setattr(model, field, data[field])
        self._session.commit()
        return document_model_to_dict(model)

    def delete(self, document_id: str) -> bool:
        deleted = (
            self._session.query(ApplicationDocumentModel)
            .filter(ApplicationDocumentModel.id == document_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)
