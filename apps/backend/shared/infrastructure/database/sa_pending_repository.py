"""SQLAlchemy-based pending repository (redirected to JobModel/CompanyModel)."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.domain.repositories.pending_repository import IPendingRepository
from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel
from shared.infrastructure.database.mappers import job_model_to_dict, company_model_to_dict


class SQLAlchemyPendingRepository(IPendingRepository):
    """SQLAlchemy implementation backed by JobModel/CompanyModel."""

    def __init__(self, session: Session):
        self._session = session

    EXCLUDED_STATUSES = {"processed"}

    def list_pending(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        if table == "pending_jobs":
            rows = self._session.query(JobModel).filter(
                JobModel.deleted == 0,
                ~JobModel.status.in_(self.EXCLUDED_STATUSES)
            ).order_by(JobModel.created_at.desc()).all()
            return [job_model_to_dict(r) for r in rows]
        elif table == "pending_companies":
            rows = self._session.query(CompanyModel).filter(
                ~CompanyModel.status.in_(self.EXCLUDED_STATUSES)
            ).order_by(CompanyModel.created_at.desc()).all()
            return [company_model_to_dict(r) for r in rows]
        return []

    def get_by_id(self, item_id: str, table: str = "pending_jobs") -> dict[str, Any] | None:
        if table == "pending_jobs":
            model = self._session.query(JobModel).filter(JobModel.id == item_id).first()
            return job_model_to_dict(model) if model else None
        elif table == "pending_companies":
            model = self._session.query(CompanyModel).filter(CompanyModel.id == int(item_id)).first()
            return company_model_to_dict(model) if model else None
        return None

    def create(self, data: dict[str, Any], table: str = "pending_jobs") -> dict[str, Any]:
        if table == "pending_jobs":
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

            from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
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

        elif table == "pending_companies":
            model = CompanyModel(
                notes=json.dumps(data.get("notes", []), ensure_ascii=False) if data.get("notes") else "[]",
                source=data.get("source", "api"),
                status="created",
            )
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)
            return company_model_to_dict(model)

        raise ValueError(f"Unknown table: {table}")

    def update_status(self, item_id: str, status: str, table: str = "pending_jobs", **fields) -> bool:
        if table == "pending_jobs":
            m = self._session.query(JobModel).filter(JobModel.id == item_id).first()
        elif table == "pending_companies":
            m = self._session.query(CompanyModel).filter(CompanyModel.id == int(item_id)).first()
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
            return self._session.query(JobModel).filter(
                JobModel.deleted == 0,
                ~JobModel.status.in_(self.EXCLUDED_STATUSES)
            ).count()
        elif table == "pending_companies":
            return self._session.query(CompanyModel).filter(
                ~CompanyModel.status.in_(self.EXCLUDED_STATUSES)
            ).count()
        return 0

    def get_by_url(self, url: str) -> dict[str, Any] | None:
        m = self._session.query(JobModel).filter(JobModel.url == url).first()
        return job_model_to_dict(m) if m else None

    def update_fields(self, item_id: str, table: str = "pending_jobs", **fields) -> bool:
        if table == "pending_jobs":
            m = self._session.query(JobModel).filter(JobModel.id == item_id).first()
        elif table == "pending_companies":
            m = self._session.query(CompanyModel).filter(CompanyModel.id == int(item_id)).first()
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
            result = self._session.query(func.max(JobModel.queue_order)).scalar()
        elif table == "pending_companies":
            result = 0
        else:
            result = 0
        return result or 0

    ACTIVE_STATUSES = {'processing'}

    def get_processing_count(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            return self._session.query(JobModel).filter(
                JobModel.deleted == 0,
                JobModel.status.in_(self.ACTIVE_STATUSES)
            ).count()
        elif table == "pending_companies":
            return self._session.query(CompanyModel).filter(
                CompanyModel.status.in_(self.ACTIVE_STATUSES)
            ).count()
        return 0

    def get_pending_count(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            return self._session.query(JobModel).filter(
                JobModel.deleted == 0,
                JobModel.status == 'pending'
            ).count()
        elif table == "pending_companies":
            return self._session.query(CompanyModel).filter(
                CompanyModel.status == 'pending'
            ).count()
        return 0

    def get_queued_count(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            return self._session.query(JobModel).filter(
                JobModel.deleted == 0,
                JobModel.status == "queued"
            ).count()
        elif table == "pending_companies":
            return self._session.query(CompanyModel).filter(
                CompanyModel.status == "queued"
            ).count()
        return 0

    def get_processing_items(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        if table == "pending_jobs":
            rows = self._session.query(JobModel).filter(
                JobModel.deleted == 0,
                JobModel.status.in_(self.ACTIVE_STATUSES)
            ).all()
            return [job_model_to_dict(r) for r in rows]
        elif table == "pending_companies":
            rows = self._session.query(CompanyModel).filter(
                CompanyModel.status.in_(self.ACTIVE_STATUSES)
            ).all()
            return [company_model_to_dict(r) for r in rows]
        return []

    def mark_processing_as_waiting(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            count = self._session.query(JobModel).filter(
                JobModel.deleted == 0,
                JobModel.status.in_(self.ACTIVE_STATUSES)
            ).update({"status": "pending"})
        elif table == "pending_companies":
            count = self._session.query(CompanyModel).filter(
                CompanyModel.status.in_(self.ACTIVE_STATUSES)
            ).update({"status": "pending"})
        else:
            count = 0
        self._session.commit()
        return count

    def reset_processing_orphans(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            count = self._session.query(JobModel).filter(
                JobModel.deleted == 0,
                JobModel.status.in_(self.ACTIVE_STATUSES)
            ).update({"status": "created"})
        elif table == "pending_companies":
            count = self._session.query(CompanyModel).filter(
                CompanyModel.status.in_(self.ACTIVE_STATUSES)
            ).update({"status": "created"})
        else:
            count = 0
        self._session.commit()
        return count

    def pick_queued_item(self, table: str = "pending_jobs") -> dict[str, Any] | None:
        if table == "pending_jobs":
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
        elif table == "pending_companies":
            model = self._session.query(CompanyModel).filter(
                CompanyModel.status == "queued"
            ).order_by(CompanyModel.id.asc()).first()
            if model:
                model.status = "processing"
                model.updated_at = datetime.now().isoformat()
                self._session.commit()
                self._session.refresh(model)
                return company_model_to_dict(model)
        return None

    def get_queued_items(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        if table == "pending_jobs":
            rows = self._session.query(JobModel).filter(
                JobModel.deleted == 0,
                JobModel.status == "queued"
            ).order_by(JobModel.queue_order.asc(), JobModel.id.asc()).all()
            return [job_model_to_dict(r) for r in rows]
        elif table == "pending_companies":
            rows = self._session.query(CompanyModel).filter(
                CompanyModel.status == "queued"
            ).order_by(CompanyModel.id.asc()).all()
            return [company_model_to_dict(r) for r in rows]
        return []

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
        if table == "pending_jobs":
            self._session.query(JobModel).filter(JobModel.id == item_id).update(updates)
        elif table == "pending_companies":
            self._session.query(CompanyModel).filter(CompanyModel.id == item_id).update(updates)
        self._session.commit()
        return True

    def get_all_for_stream(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        if table == "pending_jobs":
            rows = self._session.query(JobModel).order_by(JobModel.created_at.desc()).all()
            return [job_model_to_dict(r) for r in rows]
        elif table == "pending_companies":
            rows = self._session.query(CompanyModel).order_by(CompanyModel.created_at.desc()).all()
            return [company_model_to_dict(r) for r in rows]
        return []

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
        if table == "pending_jobs":
            m = self._session.query(JobModel).filter(JobModel.id == item_id).first()
            if m:
                m.deleted = 1
                self._session.commit()
                return True
        elif table == "pending_companies":
            m = self._session.query(CompanyModel).filter(CompanyModel.id == int(item_id)).first()
            if m:
                self._session.delete(m)
                self._session.commit()
                return True
        return False

    def create_pending_company(self, input_text: str, input_type: str, source: str, status: str = "created", notes: str = "[]", company_id: int = None, links: str = "[]") -> dict[str, Any]:
        model = CompanyModel(
            notes=notes, source=source, status=status,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return company_model_to_dict(model)
