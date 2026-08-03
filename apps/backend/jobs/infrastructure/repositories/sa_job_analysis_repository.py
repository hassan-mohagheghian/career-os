"""SQLAlchemy-based job analysis repository implementation."""

import json
from typing import Any

from sqlalchemy.orm import Session

from jobs.domain.repositories.job_analysis_repository import IJobAnalysisRepository
from jobs.infrastructure.models.job_analysis_model import JobAnalysisModel


class SQLAlchemyJobAnalysisRepository(IJobAnalysisRepository):
    """SQLAlchemy implementation of the job analysis repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: JobAnalysisModel) -> dict[str, Any]:
        return {
            "job_id": m.job_id,
            "payload": json.loads(m.payload) if m.payload else None,
            "fit_score": m.fit_score,
            "success_score": m.success_score,
            "overall_score": m.overall_score,
            "recommendation": m.recommendation,
            "apply_reason": m.apply_reason,
            "summary": m.summary,
            "prompt_version": m.prompt_version,
            "schema_version": m.schema_version,
            "generated_at": m.generated_at,
        }

    def get_by_job_id(self, job_id: str) -> dict[str, Any] | None:
        m = self._session.query(JobAnalysisModel).filter(JobAnalysisModel.job_id == job_id).first()
        return self._to_dict(m) if m else None

    def upsert_by_job_id(self, job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        existing = self._session.query(JobAnalysisModel).filter(JobAnalysisModel.job_id == job_id).first()
        if existing:
            for field in [
                "payload", "fit_score", "success_score", "overall_score",
                "recommendation", "apply_reason", "summary",
                "prompt_version", "schema_version", "generated_at",
            ]:
                if field in data:
                    setattr(existing, field, data[field])
            self._session.commit()
            self._session.refresh(existing)
            return self._to_dict(existing)
        m = JobAnalysisModel(job_id=job_id, **{k: v for k, v in data.items() if hasattr(JobAnalysisModel, k)})
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def delete_by_job_id(self, job_id: str) -> bool:
        m = self._session.query(JobAnalysisModel).filter(JobAnalysisModel.job_id == job_id).first()
        if not m:
            return False
        self._session.delete(m)
        self._session.commit()
        return True
