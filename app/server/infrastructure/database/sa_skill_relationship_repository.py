"""SQLAlchemy-based skill relationship repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from domain.repositories.skill_relationship_repository import ISkillRelationshipRepository
from infrastructure.database.models.skill_model import SkillRelationshipModel


class SQLAlchemySkillRelationshipRepository(ISkillRelationshipRepository):
    """SQLAlchemy implementation of skill relationship repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: SkillRelationshipModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "skill_name": m.skill_name,
            "related_name": m.related_name,
            "relation_type": m.relation_type,
            "confidence": m.confidence,
        }

    def get_for_skill(self, skill_name: str) -> list[dict[str, Any]]:
        rows = self._session.query(SkillRelationshipModel).filter(
            (SkillRelationshipModel.skill_name == skill_name) |
            (SkillRelationshipModel.related_name == skill_name)
        ).all()
        return [self._to_dict(r) for r in rows]

    def exists(self, skill_name: str, related_name: str, relation_type: str) -> bool:
        return self._session.query(SkillRelationshipModel).filter(
            SkillRelationshipModel.skill_name == skill_name,
            SkillRelationshipModel.related_name == related_name,
            SkillRelationshipModel.relation_type == relation_type,
        ).first() is not None

    def create(self, skill_name: str, related_name: str, relation_type: str, confidence: float = 0) -> bool:
        if self.exists(skill_name, related_name, relation_type):
            return False
        m = SkillRelationshipModel(
            skill_name=skill_name,
            related_name=related_name,
            relation_type=relation_type,
            confidence=confidence,
        )
        self._session.add(m)
        self._session.commit()
        return True

    def delete(self, rel_id: int) -> bool:
        m = self._session.query(SkillRelationshipModel).filter(SkillRelationshipModel.id == rel_id).first()
        if not m:
            return False
        self._session.delete(m)
        self._session.commit()
        return True

    def delete_all(self) -> int:
        count = self._session.query(SkillRelationshipModel).delete()
        self._session.commit()
        return count
