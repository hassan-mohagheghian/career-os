"""SQLAlchemy implementation of the skill note repository."""

from typing import Any

from sqlalchemy.orm import Session

from skills.domain.repositories.skill_note_repository import ISkillNoteRepository
from skills.infrastructure.mappers import (
    dict_to_skill_note_model,
    skill_note_model_to_dict,
)
from skills.infrastructure.models.skill_model import SkillNoteModel


class SQLAlchemySkillNoteRepository(ISkillNoteRepository):
    """SQLAlchemy implementation of the skill note repository."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_skill_note_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return skill_note_model_to_dict(model)

    def list_for_skill(self, skill_id: int) -> list[dict[str, Any]]:
        rows = (
            self._session.query(SkillNoteModel)
            .filter(SkillNoteModel.skill_id == skill_id)
            .order_by(SkillNoteModel.created_at.desc())
            .all()
        )
        return [skill_note_model_to_dict(r) for r in rows]

    def get_by_id(self, note_id: int) -> dict[str, Any] | None:
        model = (
            self._session.query(SkillNoteModel)
            .filter(SkillNoteModel.id == note_id)
            .first()
        )
        return skill_note_model_to_dict(model) if model else None

    def delete(self, note_id: int) -> bool:
        deleted = (
            self._session.query(SkillNoteModel)
            .filter(SkillNoteModel.id == note_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)
