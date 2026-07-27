"""SQLAlchemy-based tech learning repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from domain.repositories.tech_learning_repository import ITechLearningRepository
from infrastructure.database.models.misc_models import TechLearningModel


class SQLAlchemyTechLearningRepository(ITechLearningRepository):
    """SQLAlchemy implementation of tech learning repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: TechLearningModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "name": m.name,
            "priority": m.priority,
            "pl": m.pl,
            "pc": m.pc,
            "sc": m.sc,
            "dc": m.dc,
            "usage": m.usage,
            "uc": m.uc,
            "jobs": m.jobs,
            "jd": m.jd,
            "reason": m.reason,
            "action": m.action,
        }

    def get_all(self) -> list[dict[str, Any]]:
        rows = self._session.query(TechLearningModel).order_by(TechLearningModel.priority).all()
        return [self._to_dict(r) for r in rows]

    def get_by_id(self, item_id: int) -> dict[str, Any] | None:
        m = self._session.query(TechLearningModel).filter(TechLearningModel.id == item_id).first()
        return self._to_dict(m) if m else None

    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        item_id = data.get("id")
        if item_id:
            existing = self._session.query(TechLearningModel).filter(TechLearningModel.id == item_id).first()
            if existing:
                for k, v in data.items():
                    if hasattr(existing, k) and k != "id":
                        setattr(existing, k, v)
                self._session.commit()
                self._session.refresh(existing)
                return self._to_dict(existing)
        m = TechLearningModel(**{k: v for k, v in data.items() if hasattr(TechLearningModel, k)})
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)
