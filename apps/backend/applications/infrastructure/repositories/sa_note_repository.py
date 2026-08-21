"""SQLAlchemy implementation of the note repository."""

from typing import Any

from sqlalchemy.orm import Session

from applications.domain.repositories.note_repository import INoteRepository
from applications.infrastructure.mappers import (
    dict_to_note_model,
    note_model_to_dict,
)
from applications.infrastructure.models.application_model import ApplicationNoteModel


class SQLAlchemyNoteRepository(INoteRepository):
    """SQLAlchemy implementation of the note repository."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_note_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return note_model_to_dict(model)

    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(ApplicationNoteModel)
            .filter(ApplicationNoteModel.application_id == application_id)
            .order_by(ApplicationNoteModel.created_at.desc())
            .all()
        )
        return [note_model_to_dict(r) for r in rows]

    def get_by_id(self, note_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(ApplicationNoteModel)
            .filter(ApplicationNoteModel.id == note_id)
            .first()
        )
        return note_model_to_dict(model) if model else None

    def delete(self, note_id: str) -> bool:
        deleted = (
            self._session.query(ApplicationNoteModel)
            .filter(ApplicationNoteModel.id == note_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)
