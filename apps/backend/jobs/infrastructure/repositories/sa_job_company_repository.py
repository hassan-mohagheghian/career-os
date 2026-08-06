"""SQLAlchemy implementation of the job-company repository."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from sqlalchemy.orm import Session

from jobs.domain.repositories.job_company_repository import IJobCompanyRepository
from jobs.infrastructure.models.job_company_model import JobCompanyModel


class SQLAlchemyJobCompanyRepository(IJobCompanyRepository):
    """SQLAlchemy implementation of the job-company repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: JobCompanyModel) -> dict[str, Any]:
        created_at = m.created_at
        if hasattr(created_at, "isoformat"):
            created_at = created_at.isoformat()
        return {
            "id": m.id,
            "job_id": m.job_id,
            "company_id": m.company_id,
            "role": m.role,
            "company_type": m.company_type,
            "confidence": m.confidence,
            "reason": m.reason,
            "created_at": created_at,
        }

    def replace_for_job(self, job_id: str, rows: list[dict[str, Any]]) -> None:
        self._session.query(JobCompanyModel).filter(
            JobCompanyModel.job_id == job_id
        ).delete()
        for row in rows:
            self._session.add(
                JobCompanyModel(
                    job_id=job_id,
                    company_id=row["company_id"],
                    role=row.get("role", "hiring"),
                    company_type=row.get("company_type"),
                    confidence=row.get("confidence"),
                    reason=row.get("reason"),
                    created_at=datetime.now(UTC),
                )
            )
        self._session.commit()

    def list_by_job(self, job_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(JobCompanyModel)
            .filter(JobCompanyModel.job_id == job_id)
            .order_by(JobCompanyModel.id.desc())
            .all()
        )
        return [self._to_dict(r) for r in rows]

    def list_by_company(self, company_id: str, role: str | None = None) -> list[dict[str, Any]]:
        query = self._session.query(JobCompanyModel).filter(
            JobCompanyModel.company_id == company_id
        )
        if role:
            query = query.filter(JobCompanyModel.role == role)
        rows = query.order_by(JobCompanyModel.id.desc()).all()
        return [self._to_dict(r) for r in rows]

    def recruiter_hiring_pairs(self, recruiter_id: str) -> list[dict[str, Any]]:
        """For a recruiter company, return the hiring companies of the jobs it
        published: ``[{job_id, hiring_company_id}]`` (one entry per job)."""
        recruiter_job_ids = [
            r.job_id
            for r in self._session.query(JobCompanyModel).filter(
                JobCompanyModel.company_id == recruiter_id,
                JobCompanyModel.role == "recruiter",
            ).all()
        ]
        if not recruiter_job_ids:
            return []
        hiring_rows = (
            self._session.query(JobCompanyModel)
            .filter(
                JobCompanyModel.job_id.in_(recruiter_job_ids),
                JobCompanyModel.role == "hiring",
                JobCompanyModel.company_id != recruiter_id,
            )
            .all()
        )
        return [{"job_id": r.job_id, "hiring_company_id": r.company_id} for r in hiring_rows]
