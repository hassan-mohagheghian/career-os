"""SQLAlchemy-based skill roadmap progress repository implementation."""

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from skills.domain.repositories.skill_roadmap_progress_repository import ISkillRoadmapProgressRepository
from skills.infrastructure.models.skill_roadmap_models import SkillRoadmapProgressModel, SkillRoadmapModel


class SQLAlchemySkillRoadmapProgressRepository(ISkillRoadmapProgressRepository):
    """SQLAlchemy implementation of skill roadmap progress repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: SkillRoadmapProgressModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "roadmap_id": m.roadmap_id,
            "skill_name": m.skill_name,
            "completed": m.completed,
            "updated_at": m.updated_at,
        }

    def get_completed_titles(self, skill_name: str) -> list[str]:
        rows = self._session.query(SkillRoadmapModel.title).join(
            SkillRoadmapProgressModel,
            SkillRoadmapProgressModel.roadmap_id == SkillRoadmapModel.id,
        ).filter(
            SkillRoadmapModel.skill_name == skill_name,
            SkillRoadmapProgressModel.completed == 1,
        ).all()
        return [r[0] for r in rows]

    def get_by_roadmap_id(self, roadmap_id: int) -> dict[str, Any] | None:
        m = self._session.query(SkillRoadmapProgressModel).filter(
            SkillRoadmapProgressModel.roadmap_id == roadmap_id
        ).first()
        return self._to_dict(m) if m else None

    def toggle(self, roadmap_id: int, skill_name: str) -> dict[str, Any]:
        existing = self._session.query(SkillRoadmapProgressModel).filter(
            SkillRoadmapProgressModel.roadmap_id == roadmap_id
        ).first()
        if existing:
            existing.completed = 0 if existing.completed else 1
            self._session.commit()
            self._session.refresh(existing)
            return self._to_dict(existing)
        m = SkillRoadmapProgressModel(
            roadmap_id=roadmap_id,
            skill_name=skill_name,
            completed=1,
        )
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def set_completed(self, roadmap_id: int, completed: int) -> dict[str, Any]:
        existing = self._session.query(SkillRoadmapProgressModel).filter(
            SkillRoadmapProgressModel.roadmap_id == roadmap_id
        ).first()
        if existing:
            existing.completed = completed
            self._session.commit()
            self._session.refresh(existing)
            return self._to_dict(existing)
        rm = self._session.query(SkillRoadmapModel).filter(SkillRoadmapModel.id == roadmap_id).first()
        skill_name = rm.skill_name if rm else ""
        m = SkillRoadmapProgressModel(
            roadmap_id=roadmap_id,
            skill_name=skill_name,
            completed=completed,
        )
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def get_all(self) -> list[dict[str, Any]]:
        rows = self._session.query(SkillRoadmapProgressModel).all()
        return [self._to_dict(r) for r in rows]

    def get_by_skill(self, skill_name: str) -> dict[str, Any]:
        rows = self._session.query(SkillRoadmapProgressModel).filter(
            SkillRoadmapProgressModel.skill_name == skill_name
        ).all()
        return {r.roadmap_id: r.completed for r in rows}

    def get_all_aggregated(self) -> dict[str, Any]:
        total_rows = self._session.query(
            SkillRoadmapModel.skill_name,
            func.count(SkillRoadmapModel.id).label("total_count"),
        ).group_by(SkillRoadmapModel.skill_name).all()

        completed_rows = self._session.query(
            SkillRoadmapProgressModel.skill_name,
            func.count(SkillRoadmapProgressModel.id).label("completed_count"),
        ).filter(
            SkillRoadmapProgressModel.completed == 1
        ).group_by(SkillRoadmapProgressModel.skill_name).all()
        completed_map = {r[0]: r[1] for r in completed_rows}

        progress_rows = self._session.query(SkillRoadmapProgressModel).all()
        checked_map: dict[str, dict[int, int]] = {}
        for r in progress_rows:
            sname = r.skill_name
            if sname not in checked_map:
                checked_map[sname] = {}
            checked_map[sname][r.roadmap_id] = r.completed

        result = {}
        for r in total_rows:
            sname = r[0]
            tot = r[1]
            comp = completed_map.get(sname, 0)
            pct = round((comp / tot) * 100) if tot > 0 else 0
            result[sname] = {
                "total": tot,
                "completed": comp,
                "pct": pct,
                "checked": checked_map.get(sname, {}),
            }
        return result
