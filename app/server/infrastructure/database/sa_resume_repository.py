"""SQLAlchemy-based resume repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from domain.repositories.resume_repository import IResumeRepository
from infrastructure.database.models.misc_models import ResumeModel


class SQLAlchemyResumeRepository(IResumeRepository):
    """SQLAlchemy implementation of resume repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: ResumeModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "title": m.title,
            "company": m.company,
            "role": m.role,
            "content": m.content,
            "version": m.version,
            "raw_text": m.raw_text,
            "created_at": m.created_at,
            "job_num": m.job_num,
        }

    def get_all(self) -> list[dict[str, Any]]:
        rows = self._session.query(ResumeModel).order_by(ResumeModel.created_at.desc()).all()
        return [self._to_dict(r) for r in rows]

    def get_by_id(self, resume_id: str) -> dict[str, Any] | None:
        m = self._session.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
        return self._to_dict(m) if m else None

    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        resume_id = data.get("id", "")
        existing = self._session.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
        if existing:
            for field in ["title", "company", "role", "content", "version", "raw_text", "job_num"]:
                if field in data:
                    setattr(existing, field, data[field])
            self._session.commit()
            self._session.refresh(existing)
            return self._to_dict(existing)
        m = ResumeModel(**{k: v for k, v in data.items() if hasattr(ResumeModel, k)})
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def delete_by_id(self, resume_id: str) -> bool:
        m = self._session.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
        if not m:
            return False
        self._session.delete(m)
        self._session.commit()
        return True

    def get_latest_original_raw_text(self) -> str | None:
        m = self._session.query(ResumeModel).filter(
            ResumeModel.id.like("original_%")
        ).order_by(ResumeModel.version.desc()).first()
        return m.raw_text if m else None

    def get_latest_linkedin_raw_text(self) -> str | None:
        m = self._session.query(ResumeModel).filter(
            ResumeModel.id.like("linkedin_%")
        ).order_by(ResumeModel.created_at.desc()).first()
        return m.raw_text if m else None

    def delete_non_original(self) -> int:
        count = self._session.query(ResumeModel).filter(
            ResumeModel.id != "original"
        ).delete(synchronize_session=False)
        self._session.commit()
        return count

    def get_for_job(self, job_num: int) -> dict[str, Any] | None:
        m = self._session.query(ResumeModel).filter(
            ResumeModel.job_num == job_num,
            ~ResumeModel.id.like("cover_%"),
        ).order_by(ResumeModel.created_at.desc()).first()
        return self._to_dict(m) if m else None

    def get_cover_for_job(self, job_num: int) -> dict[str, Any] | None:
        m = self._session.query(ResumeModel).filter(
            ResumeModel.job_num == job_num,
            ResumeModel.id.like("cover_%"),
        ).order_by(ResumeModel.created_at.desc()).first()
        return self._to_dict(m) if m else None
