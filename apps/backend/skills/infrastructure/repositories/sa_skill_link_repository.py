"""SQLAlchemy implementation of the skill link repository."""

from typing import Any

from sqlalchemy.orm import Session

from skills.domain.repositories.skill_link_repository import ISkillLinkRepository
from skills.infrastructure.mappers import (
    dict_to_skill_link_model,
    skill_link_model_to_dict,
)
from skills.infrastructure.models.skill_model import SkillLinkModel


class SQLAlchemySkillLinkRepository(ISkillLinkRepository):
    """SQLAlchemy implementation of the skill link repository."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_skill_link_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return skill_link_model_to_dict(model)

    def list_for_skill(self, skill_id: int) -> list[dict[str, Any]]:
        rows = (
            self._session.query(SkillLinkModel)
            .filter(SkillLinkModel.skill_id == skill_id)
            .order_by(SkillLinkModel.created_at.desc())
            .all()
        )
        return [skill_link_model_to_dict(r) for r in rows]

    def get_by_id(self, link_id: int) -> dict[str, Any] | None:
        model = (
            self._session.query(SkillLinkModel)
            .filter(SkillLinkModel.id == link_id)
            .first()
        )
        return skill_link_model_to_dict(model) if model else None

    def delete(self, link_id: int) -> bool:
        deleted = (
            self._session.query(SkillLinkModel)
            .filter(SkillLinkModel.id == link_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)
