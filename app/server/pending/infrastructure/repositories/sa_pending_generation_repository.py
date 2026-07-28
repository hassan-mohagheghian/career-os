"""SQLAlchemy-based pending generation repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from pending.domain.repositories.pending_generation_repository import IPendingGenerationRepository
from pending.infrastructure.models.pending_model import PendingGenerationModel


class SQLAlchemyPendingGenerationRepository(IPendingGenerationRepository):
    """SQLAlchemy implementation of pending generation repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: PendingGenerationModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "job_num": m.job_num,
            "type": m.type,
            "status": m.status,
            "step_prepare": m.step_prepare,
            "step_context": m.step_context,
            "step_generate": m.step_generate,
            "step_save": m.step_save,
            "step_done": m.step_done,
            "result": m.result,
            "error": m.error,
            "session_id": m.session_id,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }

    def get_by_id(self, gen_id: int) -> dict[str, Any] | None:
        m = self._session.query(PendingGenerationModel).filter(PendingGenerationModel.id == gen_id).first()
        return self._to_dict(m) if m else None

    def create(self, job_num: int, gen_type: str, status: str = "queued") -> dict[str, Any]:
        m = PendingGenerationModel(job_num=job_num, type=gen_type, status=status)
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def update_fields(self, gen_id: int, **fields) -> bool:
        m = self._session.query(PendingGenerationModel).filter(PendingGenerationModel.id == gen_id).first()
        if not m:
            return False
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()
        return True

    def get_active_for_job(self, job_num: int, gen_type: str) -> dict[str, Any] | None:
        m = self._session.query(PendingGenerationModel).filter(
            PendingGenerationModel.job_num == job_num,
            PendingGenerationModel.type == gen_type,
            PendingGenerationModel.status.in_(["queued", "processing"]),
        ).first()
        return self._to_dict(m) if m else None

    def get_all_active(self) -> list[dict[str, Any]]:
        rows = self._session.query(PendingGenerationModel).filter(
            PendingGenerationModel.status.in_(["queued", "processing"])
        ).order_by(PendingGenerationModel.created_at.desc()).all()
        return [self._to_dict(r) for r in rows]

    def get_history_for_job(self, job_num: int) -> list[dict[str, Any]]:
        rows = self._session.query(PendingGenerationModel).filter(
            PendingGenerationModel.job_num == job_num
        ).order_by(PendingGenerationModel.created_at.desc()).all()
        return [self._to_dict(r) for r in rows]

    def get_active_count(self, job_num: int) -> int:
        return self._session.query(PendingGenerationModel).filter(
            PendingGenerationModel.job_num == job_num,
            PendingGenerationModel.status.in_(["queued", "processing"]),
        ).count()
