"""SQLAlchemy-based tailored document repository implementation."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from jobs.domain.repositories.tailored_document_repository import ITailoredDocumentRepository
from jobs.infrastructure.models.misc_models import ResumeModel


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
            "job_id": m.job_id,
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
            for field in ["title", "company", "role", "content", "version", "raw_text", "job_id"]:
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

    def get_for_job(self, job_id: str) -> dict[str, Any] | None:
        m = self._session.query(ResumeModel).filter(
            ResumeModel.job_id == job_id,
            ~ResumeModel.id.like("cover_%"),
        ).order_by(ResumeModel.created_at.desc()).first()
        return self._to_dict(m) if m else None

    def get_cover_for_job(self, job_id: str) -> dict[str, Any] | None:
        m = self._session.query(ResumeModel).filter(
            ResumeModel.job_id == job_id,
            ResumeModel.id.like("cover_%"),
        ).order_by(ResumeModel.created_at.desc()).first()
        return self._to_dict(m) if m else None

    def get_active_for_job(self, job_id: str, doc_type: str) -> dict[str, Any] | None:
        resume_id = f"{doc_type}_{job_id}"
        m = self._session.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
        if not m:
            return None
        state = json.loads(m.raw_text) if m.raw_text else {}
        if state.get("status") in ("queued", "processing"):
            return {"id": job_id, "job_id": job_id, "type": doc_type, "status": state.get("status")}
        return None

    def create_generation(self, job_id: str, doc_type: str) -> dict[str, Any]:
        resume_id = f"{doc_type}_{job_id}"
        now = datetime.utcnow().isoformat()
        state = json.dumps({"status": "queued", "created_at": now})
        existing = self._session.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
        if existing:
            existing.raw_text = state
            existing.content = None
            self._session.commit()
            self._session.refresh(existing)
        else:
            m = ResumeModel(
                id=resume_id,
                title=f"{doc_type} for job {job_id}",
                job_id=job_id,
                raw_text=state,
            )
            self._session.add(m)
            self._session.commit()
            self._session.refresh(m)
        return {"id": job_id, "job_id": job_id, "type": doc_type, "status": "queued"}

    def get_all_active(self) -> list[dict[str, Any]]:
        return []

    def get_history_for_job(self, job_id: str) -> list[dict[str, Any]]:
        rows = self._session.query(ResumeModel).filter(
            ResumeModel.job_id == job_id
        ).order_by(ResumeModel.created_at.desc()).all()
        return [self._to_dict(r) for r in rows]
