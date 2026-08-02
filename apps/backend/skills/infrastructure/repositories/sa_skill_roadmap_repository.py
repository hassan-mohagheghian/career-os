"""SQLAlchemy-based skill roadmap repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from skills.domain.repositories.skill_roadmap_repository import ISkillRoadmapRepository
from shared.infrastructure.database.models.misc_models import SkillRoadmapModel


class SQLAlchemySkillRoadmapRepository(ISkillRoadmapRepository):
    """SQLAlchemy implementation of skill roadmap repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: SkillRoadmapModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "skill_name": m.skill_name,
            "parent_id": m.parent_id,
            "title": m.title,
            "description": m.description,
            "level": m.level,
            "sort_order": m.sort_order,
            "version": m.version,
            "numbering": m.numbering,
            "created_at": m.created_at,
        }

    def get_by_skill_name(self, skill_name: str) -> list[dict[str, Any]]:
        rows = self._session.query(SkillRoadmapModel).filter(
            SkillRoadmapModel.skill_name == skill_name
        ).order_by(SkillRoadmapModel.sort_order, SkillRoadmapModel.id).all()
        return [self._to_dict(r) for r in rows]

    def get_by_id(self, roadmap_id: int) -> dict[str, Any] | None:
        m = self._session.query(SkillRoadmapModel).filter(SkillRoadmapModel.id == roadmap_id).first()
        return self._to_dict(m) if m else None

    def delete_by_skill_name(self, skill_name: str) -> int:
        count = self._session.query(SkillRoadmapModel).filter(
            SkillRoadmapModel.skill_name == skill_name
        ).delete()
        self._session.commit()
        return count

    def get_max_version(self, skill_name: str) -> int:
        from sqlalchemy import func
        result = self._session.query(func.max(SkillRoadmapModel.version)).filter(
            SkillRoadmapModel.skill_name == skill_name
        ).scalar()
        return result or 0

    def insert_items(self, skill_name: str, items: list[dict[str, Any]], version: int) -> int:
        count = 0
        for item in items:
            m = SkillRoadmapModel(
                skill_name=skill_name,
                parent_id=item.get("parent_id"),
                title=item.get("title", ""),
                description=item.get("description", ""),
                level=item.get("level", 0),
                sort_order=item.get("sort_order", 0),
                version=version,
                numbering=item.get("numbering", ""),
            )
            self._session.add(m)
            count += 1
        self._session.commit()
        return count

    def get_all(self) -> list[dict[str, Any]]:
        rows = self._session.query(SkillRoadmapModel).order_by(SkillRoadmapModel.skill_name).all()
        return [self._to_dict(r) for r in rows]
