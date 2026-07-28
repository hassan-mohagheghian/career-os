"""SQLAlchemy-based career insight run repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from career.domain.repositories.career_insight_run_repository import ICareerInsightRunRepository
from career.infrastructure.models.insight_model import CareerInsightRunModel


class SQLAlchemyCareerInsightRunRepository(ICareerInsightRunRepository):
    """SQLAlchemy implementation of career insight run repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: CareerInsightRunModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "insight_type": m.insight_type,
            "version": m.version,
            "status": m.status,
            "started_at": m.started_at,
            "completed_at": m.completed_at,
            "error_message": m.error_message,
            "metadata": m.metadata_json,
            "session_id": m.session_id,
        }

    def create(self, insight_type: str, version: int = 1, status: str = "pending", session_id: str | None = None) -> dict[str, Any]:
        m = CareerInsightRunModel(
            insight_type=insight_type,
            version=version,
            status=status,
            session_id=session_id,
        )
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def complete(self, run_id: int, status: str, error_message: str | None = None, session_id: str | None = None) -> bool:
        m = self._session.query(CareerInsightRunModel).filter(CareerInsightRunModel.id == run_id).first()
        if not m:
            return False
        from datetime import datetime
        m.status = status
        m.completed_at = datetime.now().isoformat()
        if error_message:
            m.error_message = error_message
        if session_id:
            m.session_id = session_id
        self._session.commit()
        return True

    def update_session_id(self, run_id: int, session_id: str) -> bool:
        m = self._session.query(CareerInsightRunModel).filter(CareerInsightRunModel.id == run_id).first()
        if not m:
            return False
        m.session_id = session_id
        self._session.commit()
        return True

    def get_latest_processing(self, insight_type: str | None = None) -> dict[str, Any] | None:
        q = self._session.query(CareerInsightRunModel).filter(
            CareerInsightRunModel.status == "processing"
        )
        if insight_type:
            q = q.filter(CareerInsightRunModel.insight_type == insight_type)
        m = q.order_by(CareerInsightRunModel.id.desc()).first()
        return self._to_dict(m) if m else None

    def cleanup_stale_runs(self, cutoff: str) -> int:
        count = self._session.query(CareerInsightRunModel).filter(
            CareerInsightRunModel.status == "processing",
            CareerInsightRunModel.started_at < cutoff,
        ).update({"status": "failed", "error_message": "Stale run cleaned up"})
        self._session.commit()
        return count

    def cancel_stale_run(self, insight_type: str) -> bool:
        m = self._session.query(CareerInsightRunModel).filter(
            CareerInsightRunModel.insight_type == insight_type,
            CareerInsightRunModel.status == "processing",
        ).order_by(CareerInsightRunModel.id.desc()).first()
        if not m:
            return False
        m.status = "cancelled"
        self._session.commit()
        return True

    def get_runs(self, insight_type: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        q = self._session.query(CareerInsightRunModel)
        if insight_type:
            q = q.filter(CareerInsightRunModel.insight_type == insight_type)
        rows = q.order_by(CareerInsightRunModel.id.desc()).offset(offset).limit(limit).all()
        return [self._to_dict(r) for r in rows]

    def get_total_count(self, insight_type: str | None = None) -> int:
        q = self._session.query(CareerInsightRunModel)
        if insight_type:
            q = q.filter(CareerInsightRunModel.insight_type == insight_type)
        return q.count()

    def get_latest_session_id(self, insight_type: str) -> str | None:
        m = self._session.query(CareerInsightRunModel).filter(
            CareerInsightRunModel.insight_type == insight_type,
            CareerInsightRunModel.status.in_(["processing", "completed"]),
        ).order_by(CareerInsightRunModel.id.desc()).first()
        return m.session_id if m else None
