"""SQLAlchemy-based pending repository implementation."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from processing.domain.repositories.pending_repository import IPendingRepository
from processing.infrastructure.models.pending_model import PendingJobModel, PendingCompanyModel
from shared.infrastructure.database.mappers import pending_job_model_to_dict, pending_company_model_to_dict


class SQLAlchemyPendingRepository(IPendingRepository):
    """SQLAlchemy implementation of pending repository."""

    def __init__(self, session: Session):
        self._session = session

    EXCLUDED_STATUSES = {"done", "completed"}

    def list_pending(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        if table == "pending_jobs":
            rows = self._session.query(PendingJobModel).filter(
                ~PendingJobModel.status.in_(self.EXCLUDED_STATUSES)
            ).order_by(PendingJobModel.created_at.desc()).all()
            return [pending_job_model_to_dict(r) for r in rows]
        elif table == "pending_companies":
            rows = self._session.query(PendingCompanyModel).filter(
                ~PendingCompanyModel.status.in_(self.EXCLUDED_STATUSES)
            ).order_by(PendingCompanyModel.created_at.desc()).all()
            return [pending_company_model_to_dict(r) for r in rows]
        return []

    def get_by_id(self, item_id: str, table: str = "pending_jobs") -> dict[str, Any] | None:
        if table == "pending_jobs":
            model = self._session.query(PendingJobModel).filter(PendingJobModel.id == int(item_id)).first()
            return pending_job_model_to_dict(model) if model else None
        elif table == "pending_companies":
            model = self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == int(item_id)).first()
            return pending_company_model_to_dict(model) if model else None
        return None

    def create(self, data: dict[str, Any], table: str = "pending_jobs") -> dict[str, Any]:
        if table == "pending_jobs":
            url = data.get("url", "")
            existing = self._session.query(PendingJobModel).filter(PendingJobModel.url == url).first()
            if existing:
                existing.status = "created"
                existing.previous_status = existing.status
                existing.error = None
                existing.source = data.get("source", "api")
                existing.company = data.get("company", "")
                existing.queue_order = 0
                existing.workflow_log = "[]"
                existing.updated_at = datetime.now().isoformat()
                self._session.commit()
                self._session.refresh(existing)
                return pending_job_model_to_dict(existing)

            model = PendingJobModel(
                url=url,
                source=data.get("source", "api"),
                company=data.get("company", ""),
                status="created",
                notes=json.dumps(data.get("notes", "[]")) if isinstance(data.get("notes"), (list, dict)) else data.get("notes", "[]"),
                links=json.dumps(data.get("links", "[]")) if isinstance(data.get("links"), (list, dict)) else data.get("links", "[]"),
            )
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)
            return pending_job_model_to_dict(model)

        elif table == "pending_companies":
            model = PendingCompanyModel(
                input_text=data.get("name", data.get("input_text", "")),
                input_type=data.get("input_type", "url"),
                source=data.get("source", "api"),
                status="created",
                notes=json.dumps(data.get("notes", "[]")) if isinstance(data.get("notes"), (list, dict)) else data.get("notes", "[]"),
                links=json.dumps(data.get("links", "[]")) if isinstance(data.get("links"), (list, dict)) else data.get("links", "[]"),
            )
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)
            return pending_company_model_to_dict(model)

        raise ValueError(f"Unknown table: {table}")

    def update_status(self, item_id: str, status: str, table: str = "pending_jobs", **fields) -> bool:
        if table == "pending_jobs":
            m = self._session.query(PendingJobModel).filter(PendingJobModel.id == int(item_id)).first()
        elif table == "pending_companies":
            m = self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == int(item_id)).first()
        else:
            return False
        if not m:
            return False
        m.status = status
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()
        return True

    def count_pending(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            return self._session.query(PendingJobModel).filter(
                ~PendingJobModel.status.in_(self.EXCLUDED_STATUSES)
            ).count()
        elif table == "pending_companies":
            return self._session.query(PendingCompanyModel).filter(
                ~PendingCompanyModel.status.in_(self.EXCLUDED_STATUSES)
            ).count()
        return 0

    # ── Extended methods for queue and services ─────────────────────

    def get_by_url(self, url: str) -> dict[str, Any] | None:
        m = self._session.query(PendingJobModel).filter(PendingJobModel.url == url).first()
        return pending_job_model_to_dict(m) if m else None

    def update_fields(self, item_id: int, table: str = "pending_jobs", **fields) -> bool:
        if table == "pending_jobs":
            m = self._session.query(PendingJobModel).filter(PendingJobModel.id == item_id).first()
        elif table == "pending_companies":
            m = self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == item_id).first()
        else:
            return False
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
        if table == "pending_jobs":
            result = self._session.query(func.max(PendingJobModel.queue_order)).scalar()
        elif table == "pending_companies":
            result = 0
        else:
            result = 0
        return result or 0

    ACTIVE_STATUSES = {'starting', 'fetching', 'analyzing', 'generating', 'finalizing'}

    def get_processing_count(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            return self._session.query(PendingJobModel).filter(
                PendingJobModel.status.in_(self.ACTIVE_STATUSES)
            ).count()
        elif table == "pending_companies":
            return self._session.query(PendingCompanyModel).filter(
                PendingCompanyModel.status.in_(self.ACTIVE_STATUSES)
            ).count()
        return 0

    def get_queued_count(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            return self._session.query(PendingJobModel).filter(PendingJobModel.status == "queued").count()
        elif table == "pending_companies":
            return self._session.query(PendingCompanyModel).filter(PendingCompanyModel.status == "queued").count()
        return 0

    def get_processing_items(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        if table == "pending_jobs":
            rows = self._session.query(PendingJobModel).filter(
                PendingJobModel.status.in_(self.ACTIVE_STATUSES)
            ).all()
            return [pending_job_model_to_dict(r) for r in rows]
        elif table == "pending_companies":
            rows = self._session.query(PendingCompanyModel).filter(
                PendingCompanyModel.status.in_(self.ACTIVE_STATUSES)
            ).all()
            return [pending_company_model_to_dict(r) for r in rows]
        return []

    def mark_processing_as_waiting(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            count = self._session.query(PendingJobModel).filter(
                PendingJobModel.status.in_(self.ACTIVE_STATUSES)
            ).update({"status": "waiting", "previous_status": PendingJobModel.status})
        elif table == "pending_companies":
            count = self._session.query(PendingCompanyModel).filter(
                PendingCompanyModel.status.in_(self.ACTIVE_STATUSES)
            ).update({"status": "waiting", "previous_status": PendingCompanyModel.status})
        else:
            count = 0
        self._session.commit()
        return count

    def reset_processing_orphans(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            count = self._session.query(PendingJobModel).filter(
                PendingJobModel.status.in_(self.ACTIVE_STATUSES)
            ).update({"status": "created", "previous_status": PendingJobModel.status})
        elif table == "pending_companies":
            count = self._session.query(PendingCompanyModel).filter(
                PendingCompanyModel.status.in_(self.ACTIVE_STATUSES)
            ).update({"status": "created", "previous_status": PendingCompanyModel.status})
        else:
            count = 0
        self._session.commit()
        return count

    def pick_queued_item(self, table: str = "pending_jobs") -> dict[str, Any] | None:
        if table == "pending_jobs":
            model = self._session.query(PendingJobModel).filter(
                PendingJobModel.status == "queued"
            ).order_by(
                PendingJobModel.queue_order.asc(),
                PendingJobModel.id.asc()
            ).first()
            if model:
                model.status = "starting"
                model.previous_status = "queued"
                model.updated_at = datetime.now().isoformat()
                self._session.commit()
                self._session.refresh(model)
                return pending_job_model_to_dict(model)
        elif table == "pending_companies":
            model = self._session.query(PendingCompanyModel).filter(
                PendingCompanyModel.status == "queued"
            ).order_by(PendingCompanyModel.id.asc()).first()
            if model:
                model.status = "starting"
                model.previous_status = "queued"
                model.updated_at = datetime.now().isoformat()
                self._session.commit()
                self._session.refresh(model)
                return pending_company_model_to_dict(model)
        return None

    def get_queued_items(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        if table == "pending_jobs":
            rows = self._session.query(PendingJobModel).filter(
                PendingJobModel.status == "queued"
            ).order_by(PendingJobModel.queue_order.asc(), PendingJobModel.id.asc()).all()
            return [pending_job_model_to_dict(r) for r in rows]
        elif table == "pending_companies":
            rows = self._session.query(PendingCompanyModel).filter(
                PendingCompanyModel.status == "queued"
            ).order_by(PendingCompanyModel.id.asc()).all()
            return [pending_company_model_to_dict(r) for r in rows]
        return []

    def reset_steps(self, item_id: int, version: int, table: str = "pending_jobs", keep_status: bool = False) -> bool:
        if table == "pending_jobs":
            updates = {
                "step_fetch": 0, "step_analyze": 0, "step_resume": 0, "step_cover": 0,
                "step_db": 0, "step_done": 0, "step_extract_raw": 0, "step_extract_struct": 0,
                "error": None, "version": version, "workflow_log": "[]", "current_node": None,
                "retry_count": 0, "failure_details": None,
            }
            if not keep_status:
                updates["status"] = "created"
            self._session.query(PendingJobModel).filter(PendingJobModel.id == item_id).update(updates)
        elif table == "pending_companies":
            updates = {
                "step_fetch": 0, "step_extract": 0, "step_analyze": 0, "step_save": 0, "step_done": 0,
                "error": None, "version": version, "workflow_log": "[]", "current_node": None,
                "retry_count": 0, "failure_details": None,
            }
            if not keep_status:
                updates["status"] = "created"
            self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == item_id).update(updates)
        self._session.commit()
        return True

    def get_all_for_stream(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        if table == "pending_jobs":
            rows = self._session.query(PendingJobModel).order_by(PendingJobModel.created_at.desc()).all()
            return [pending_job_model_to_dict(r) for r in rows]
        elif table == "pending_companies":
            rows = self._session.query(PendingCompanyModel).order_by(PendingCompanyModel.created_at.desc()).all()
            return [pending_company_model_to_dict(r) for r in rows]
        return []

    def get_by_url_pending(self, url: str) -> dict[str, Any] | None:
        m = self._session.query(PendingJobModel).filter(PendingJobModel.url == url).first()
        return pending_job_model_to_dict(m) if m else None

    def create_pending_job(self, url: str, source: str, company: str, status: str = "created") -> dict[str, Any]:
        model = PendingJobModel(url=url, source=source, company=company, status=status)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return pending_job_model_to_dict(model)

    def delete(self, item_id: int, table: str = "pending_jobs") -> bool:
        if table == "pending_jobs":
            m = self._session.query(PendingJobModel).filter(PendingJobModel.id == item_id).first()
        elif table == "pending_companies":
            m = self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == item_id).first()
        else:
            return False
        if not m:
            return False
        self._session.delete(m)
        self._session.commit()
        return True

    def create_pending_company(self, input_text: str, input_type: str, source: str, status: str = "created", notes: str = "[]", company_id: int = None, links: str = "[]") -> dict[str, Any]:
        model = PendingCompanyModel(
            input_text=input_text, input_type=input_type, source=source, status=status, notes=notes,
            company_id=company_id, links=links,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return pending_company_model_to_dict(model)
