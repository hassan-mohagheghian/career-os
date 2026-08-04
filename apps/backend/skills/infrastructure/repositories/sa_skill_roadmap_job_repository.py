"""SQLAlchemy-based skill roadmap job repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from skills.domain.repositories.skill_roadmap_job_repository import ISkillRoadmapJobRepository
from skills.infrastructure.models.skill_roadmap_models import SkillRoadmapJobModel


class SQLAlchemySkillRoadmapJobRepository(ISkillRoadmapJobRepository):
    """SQLAlchemy implementation of skill roadmap job repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: SkillRoadmapJobModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "skill_name": m.skill_name,
            "job_type": m.job_type,
            "status": m.status,
            "step": m.step,
            "total_steps": m.total_steps,
            "message": m.message,
            "version": m.version,
            "count": m.count,
            "error": m.error,
            "session_id": m.session_id,
            "provider_name": m.provider_name,
            "pid": m.pid,
            "started_at": m.started_at,
            "completed_at": m.completed_at,
            "created_at": m.created_at,
        }

    def create(self, skill_name: str, job_type: str = "generate", status: str = "queued", **kwargs) -> dict[str, Any]:
        m = SkillRoadmapJobModel(
            skill_name=skill_name,
            job_type=job_type,
            status=status,
            **{k: v for k, v in kwargs.items() if hasattr(SkillRoadmapJobModel, k)},
        )
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def update(self, job_id: int, **fields) -> bool:
        m = self._session.query(SkillRoadmapJobModel).filter(SkillRoadmapJobModel.id == job_id).first()
        if not m:
            return False
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()
        return True

    def get_latest_for_skill(self, skill_name: str) -> dict[str, Any] | None:
        m = self._session.query(SkillRoadmapJobModel).filter(
            SkillRoadmapJobModel.skill_name == skill_name
        ).order_by(SkillRoadmapJobModel.created_at.desc()).first()
        return self._to_dict(m) if m else None

    def get_all(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._session.query(SkillRoadmapJobModel).order_by(
            SkillRoadmapJobModel.created_at.desc()
        ).limit(limit).all()
        return [self._to_dict(r) for r in rows]

    def get_for_skill(self, skill_name: str, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._session.query(SkillRoadmapJobModel).filter(
            SkillRoadmapJobModel.skill_name == skill_name
        ).order_by(SkillRoadmapJobModel.created_at.desc()).limit(limit).all()
        return [self._to_dict(r) for r in rows]
