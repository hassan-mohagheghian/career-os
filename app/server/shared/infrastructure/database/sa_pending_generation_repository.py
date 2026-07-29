"""Pending generation repository - DEPRECATED.

The pending_generations table has been removed.
Functionality uses the resumes table via SQLAlchemyTailoredDocumentRepository.
"""
import json
from typing import Any

from jobs.infrastructure.repositories.sa_tailored_document_repository import SQLAlchemyTailoredDocumentRepository as _Base
from shared.infrastructure.database.models.misc_models import ResumeModel


class SQLAlchemyPendingGenerationRepository(_Base):
    """Deprecated wrapper — methods delegate to resumes table via parent."""

    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn("pending_generations is deprecated, use jobs tailored document context instead", DeprecationWarning, stacklevel=2)
        super().__init__(*args, **kwargs)

    def get_by_id(self, gen_id: int) -> dict[str, Any] | None:
        m = self._session.query(ResumeModel).filter(ResumeModel.job_num == gen_id).order_by(ResumeModel.created_at.desc()).first()
        if not m:
            return None
        gen_type = "resume" if m.id and m.id.startswith("resume_") else "cover" if m.id and m.id.startswith("cover_") else "unknown"
        state = json.loads(m.raw_text) if m.raw_text else {}
        return {
            "id": gen_id,
            "job_num": gen_id,
            "type": gen_type,
            "status": state.get("status", "queued"),
        }

    def create(self, job_num: int, gen_type: str, status: str = "queued") -> dict[str, Any]:
        return self.create_generation(job_num, gen_type)

    def update_fields(self, gen_id: int, **fields) -> bool:
        m = self._session.query(ResumeModel).filter(ResumeModel.job_num == gen_id).order_by(ResumeModel.created_at.desc()).first()
        if not m:
            return False
        state = json.loads(m.raw_text) if m.raw_text else {}
        state.update(fields)
        state["updated_at"] = __import__("datetime").datetime.utcnow().isoformat()
        m.raw_text = json.dumps(state)
        self._session.commit()
        return True


__all__ = ["SQLAlchemyPendingGenerationRepository"]
