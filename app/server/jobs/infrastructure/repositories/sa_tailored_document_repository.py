"""SQLAlchemy-based tailored document repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from jobs.domain.repositories.tailored_document_repository import ITailoredDocumentRepository
from shared.infrastructure.database.models.misc_models import ResumeModel


class SQLAlchemyTailoredDocumentRepository(ITailoredDocumentRepository):
    """SQLAlchemy implementation of tailored document repository."""

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

    def get_by_id(self, doc_id: str) -> dict[str, Any] | None:
        m = self._session.query(ResumeModel).filter(ResumeModel.id == doc_id).first()
        return self._to_dict(m) if m else None

    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        doc_id = data.get("id", "")
        existing = self._session.query(ResumeModel).filter(ResumeModel.id == doc_id).first()
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

    def delete_by_id(self, doc_id: str) -> bool:
        m = self._session.query(ResumeModel).filter(ResumeModel.id == doc_id).first()
        if not m:
            return False
        self._session.delete(m)
        self._session.commit()
        return True

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

    def get_active_for_job(self, job_num: int, doc_type: str) -> dict[str, Any] | None:
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        pending_repo = SQLAlchemyPendingGenerationRepository(self._session)
        return pending_repo.get_active_for_job(job_num, doc_type)

    def create_generation(self, job_num: int, doc_type: str) -> dict[str, Any]:
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        pending_repo = SQLAlchemyPendingGenerationRepository(self._session)
        return pending_repo.create(job_num=job_num, gen_type=doc_type)

    def get_all_active(self) -> list[dict[str, Any]]:
        return []

    def get_history_for_job(self, job_num: int) -> list[dict[str, Any]]:
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        pending_repo = SQLAlchemyPendingGenerationRepository(self._session)
        return pending_repo.get_history_for_job(job_num)
