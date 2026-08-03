"""SQLAlchemy-based summary repository implementation."""

from typing import Any

from sqlalchemy import case
from sqlalchemy.orm import Session

from jobs.domain.repositories.summary_repository import ISummaryRepository
from shared.infrastructure.database.models.misc_models import SummaryModel


class SQLAlchemySummaryRepository(ISummaryRepository):
    """SQLAlchemy implementation of summary repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: SummaryModel) -> dict[str, Any]:
        return {
            "job_id": m.job_id,
            "company": m.company,
            "match": m.match,
            "score": m.score,
            "summary": m.summary,
            "stack": m.stack,
            "resumeFit": m.resumeFit,
            "note": m.note,
            "url": m.url,
        }

    def get_by_job_id(self, job_id: str) -> dict[str, Any] | None:
        m = self._session.query(SummaryModel).filter(SummaryModel.job_id == job_id).first()
        return self._to_dict(m) if m else None

    def get_all(self) -> list[dict[str, Any]]:
        grade_order = case(
            (SummaryModel.score == "A++", 7),
            (SummaryModel.score == "A+", 6),
            (SummaryModel.score == "A", 5),
            (SummaryModel.score == "B", 4),
            (SummaryModel.score == "C", 3),
            (SummaryModel.score == "D", 2),
            (SummaryModel.score == "E", 1),
            else_=0,
        )
        rows = self._session.query(SummaryModel).order_by(grade_order.desc()).all()
        return [self._to_dict(r) for r in rows]

    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        job_id = data.get("job_id")
        existing = self._session.query(SummaryModel).filter(SummaryModel.job_id == job_id).first()
        if existing:
            for field in ["company", "match", "score", "summary", "stack", "resumeFit", "note", "url"]:
                if field in data:
                    setattr(existing, field, data[field])
            self._session.commit()
            self._session.refresh(existing)
            return self._to_dict(existing)
        m = SummaryModel(**{k: v for k, v in data.items() if hasattr(SummaryModel, k)})
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def delete_by_num(self, job_id: str) -> bool:
        m = self._session.query(SummaryModel).filter(SummaryModel.job_id == job_id).first()
        if not m:
            return False
        self._session.delete(m)
        self._session.commit()
        return True

    def delete_all(self) -> int:
        count = self._session.query(SummaryModel).delete()
        self._session.commit()
        return count
