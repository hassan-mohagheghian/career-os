"""SQLAlchemy-based skill alias repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from skills.domain.repositories.skill_alias_repository import ISkillAliasRepository
from skills.infrastructure.models.skill_model import SkillAliasModel, SkillModel


class SQLAlchemySkillAliasRepository(ISkillAliasRepository):
    """SQLAlchemy implementation of skill alias repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: SkillAliasModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "skill_id": m.skill_id,
            "alias_name": m.alias_name,
            "normalized_name": m.normalized_name,
            "created_at": m.created_at,
        }

    def get_by_skill_id(self, skill_id: int) -> list[dict[str, Any]]:
        rows = self._session.query(SkillAliasModel).filter(
            SkillAliasModel.skill_id == skill_id
        ).all()
        return [self._to_dict(r) for r in rows]

    def resolve_name(self, alias_name: str) -> dict[str, Any] | None:
        alias = self._session.query(SkillAliasModel).filter(
            SkillAliasModel.alias_name == alias_name
        ).first()
        if not alias:
            return None
        skill = self._session.query(SkillModel).filter(SkillModel.id == alias.skill_id).first()
        if not skill:
            return None
        return {"skill_id": skill.id, "name": skill.name, "alias_name": alias.alias_name}

    def create(self, skill_id: int, alias_name: str, normalized_name: str = "") -> dict[str, Any]:
        m = SkillAliasModel(
            skill_id=skill_id,
            alias_name=alias_name,
            normalized_name=normalized_name or alias_name.lower(),
        )
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def exists(self, skill_id: int, alias_name: str) -> bool:
        return self._session.query(SkillAliasModel).filter(
            SkillAliasModel.skill_id == skill_id,
            SkillAliasModel.alias_name == alias_name,
        ).first() is not None

    def delete_by_skill_id(self, skill_id: int) -> int:
        count = self._session.query(SkillAliasModel).filter(
            SkillAliasModel.skill_id == skill_id
        ).delete()
        self._session.commit()
        return count
