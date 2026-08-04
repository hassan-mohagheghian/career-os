"""SQLAlchemy-based pending jobs repository (backed by JobModel)."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.domain.repositories.pending_repository import IPendingRepository
from jobs.infrastructure.models.job_model import JobModel
from jobs.infrastructure.mappers import job_model_to_dict
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository


class SQLAlchemyPendingJobRepository(IPendingRepository):
    """SQLAlchemy implementation of the pending job intake queue."""

    def __init__(self, session: Session):
        self._session = session

    EXCLUDED_STATUSES = {"processed"}

    def list_pending(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            ~JobModel.status.in_(self.EXCLUDED_STATUSES)
        ).order_by(JobModel.created_at.desc()).all()
        return [job_model_to_dict(r) for r in rows]

    def get_by_id(self, item_id: str, table: str = "pending_jobs") -> dict[str, Any] | None:
        model = self._session.query(JobModel).filter(JobModel.id == item_id).first()
        return job_model_to_dict(model) if model else None

    def create(self, data: dict[str, Any], table: str = "pending_jobs") -> dict[str, Any]:
        url = data.get("url", "")
        existing = self._session.query(JobModel).filter(JobModel.url == url, JobModel.deleted == 0).first()
        if existing:
            existing.status = "created"
            existing.error = None
            existing.source = data.get("source", "api")
            existing.queue_order = 0
            existing.workflow_log = "[]"
            existing.updated_at = datetime.now().isoformat()
            self._session.commit()
            self._session.refresh(existing)
            return job_model_to_dict(existing)

        job_repo = SQLAlchemyJobRepository(self._session)
        model = JobModel(
            url=url,
            source=data.get("source", "api"),
            company=data.get("company", ""),
            status="created",
            notes=json.dumps(data.get("notes", []), ensure_ascii=False) if data.get("notes") else "[]",
            links=json.dumps(data.get("links", []), ensure_ascii=False) if data.get("links") else "[]",
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return job_model_to_dict(model)

    def update_status(self, item_id: str, status: str, table: str = "pending_jobs", **fields) -> bool:
        m = self._session.query(JobModel).filter(JobModel.id == item_id).first()
        if not m:
            return False
        m.status = status
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()
        return True

    def count_pending(self, table: str = "pending_jobs") -> int:
        return self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            ~JobModel.status.in_(self.EXCLUDED_STATUSES)
        ).count()

    def get_by_url(self, url: str) -> dict[str, Any] | None:
        m = self._session.query(JobModel).filter(JobModel.url == url).first()
        return job_model_to_dict(m) if m else None

    def update_fields(self, item_id: str, table: str = "pending_jobs", **fields) -> bool:
        m = self._session.query(JobModel).filter(JobModel.id == item_id).first()
        if not m:
            return False
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()
        return True

    def update_step(self, item_id: int, step_field: str, value: int, table: str = "pending_jobs", **extra) -> bool:
        fields = {step_field: value}
        fields.update(extra)
        return self.update_fields(item_id, table, **fields)

    def save_session_id(self, item_id: int, session_id: str, table: str = "pending_jobs") -> bool:
        return self.update_fields(item_id, table, session_id=session_id)

    def update_workflow_log(self, item_id: int, log_json: str, table: str = "pending_jobs") -> bool:
        return self.update_fields(item_id, table, workflow_log=log_json)

    def get_max_queue_order(self, table: str = "pending_jobs") -> int:
        result = self._session.query(func.max(JobModel.queue_order)).scalar()
        return result or 0

    ACTIVE_STATUSES = {'processing'}

    def get_processing_count(self, table: str = "pending_jobs") -> int:
        return self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status.in_(self.ACTIVE_STATUSES)
        ).count()

    def get_pending_count(self, table: str = "pending_jobs") -> int:
        return self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == 'pending'
        ).count()

    def get_queued_count(self, table: str = "pending_jobs") -> int:
        return self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == "queued"
        ).count()

    def get_processing_items(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status.in_(self.ACTIVE_STATUSES)
        ).all()
        return [job_model_to_dict(r) for r in rows]

    def mark_processing_as_waiting(self, table: str = "pending_jobs") -> int:
        count = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status.in_(self.ACTIVE_STATUSES)
        ).update({"status": "pending"})
        self._session.commit()
        return count

    def reset_processing_orphans(self, table: str = "pending_jobs") -> int:
        count = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status.in_(self.ACTIVE_STATUSES)
        ).update({"status": "created"})
        self._session.commit()
        return count

    def pick_queued_item(self, table: str = "pending_jobs") -> dict[str, Any] | None:
        model = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == "queued"
        ).order_by(
            JobModel.queue_order.asc(),
            JobModel.id.asc()
        ).first()
        if model:
            model.status = "processing"
            model.updated_at = datetime.now().isoformat()
            self._session.commit()
            self._session.refresh(model)
            return job_model_to_dict(model)
        return None

    def get_queued_items(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == "queued"
        ).order_by(JobModel.queue_order.asc(), JobModel.id.asc()).all()
        return [job_model_to_dict(r) for r in rows]

    def reset_steps(self, item_id: int, version: int, table: str = "pending_jobs", keep_status: bool = False) -> bool:
        updates = {
            "error": None,
            "workflow_log": "[]",
            "current_node": None,
            "retry_count": 0,
            "failure_reason": None,
        }
        if not keep_status:
            updates["status"] = "created"
        self._session.query(JobModel).filter(JobModel.id == item_id).update(updates)
        self._session.commit()
        return True

    def get_all_for_stream(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).order_by(JobModel.created_at.desc()).all()
        return [job_model_to_dict(r) for r in rows]

    def get_by_url_pending(self, url: str) -> dict[str, Any] | None:
        m = self._session.query(JobModel).filter(JobModel.url == url).first()
        return job_model_to_dict(m) if m else None

    def create_pending_job(self, url: str, source: str, company: str, status: str = "created") -> dict[str, Any]:
        model = JobModel(url=url, source=source, company=company, status=status)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return job_model_to_dict(model)

    def delete(self, item_id: str, table: str = "pending_jobs") -> bool:
        m = self._session.query(JobModel).filter(JobModel.id == item_id).first()
        if m:
            m.deleted = 1
            self._session.commit()
            return True
        return False
