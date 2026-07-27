"""SQLAlchemy-based pending repository implementation."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from domain.repositories.pending_repository import IPendingRepository
from infrastructure.database.models.pending_model import PendingJobModel, PendingCompanyModel
from infrastructure.database.mappers import pending_job_model_to_dict, pending_company_model_to_dict


class SQLAlchemyPendingRepository(IPendingRepository):
    """SQLAlchemy implementation of pending repository."""

    def __init__(self, session: Session):
        self._session = session

    def list_pending(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        if table == "pending_jobs":
            rows = self._session.query(PendingJobModel).filter(
                PendingJobModel.status != "done"
            ).order_by(PendingJobModel.created_at.desc()).all()
            return [pending_job_model_to_dict(r) for r in rows]
        elif table == "pending_companies":
            rows = self._session.query(PendingCompanyModel).filter(
                PendingCompanyModel.status != "done"
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
                existing.status = "pending"
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
                status="pending",
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
                status="pending",
                notes=json.dumps(data.get("notes", "[]")) if isinstance(data.get("notes"), (list, dict)) else data.get("notes", "[]"),
                links=json.dumps(data.get("links", "[]")) if isinstance(data.get("links"), (list, dict)) else data.get("links", "[]"),
            )
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)
            return pending_company_model_to_dict(model)

        raise ValueError(f"Unknown table: {table}")

    def update_status(self, item_id: str, status: str, table: str = "pending_jobs") -> bool:
        if table == "pending_jobs":
            self._session.query(PendingJobModel).filter(PendingJobModel.id == int(item_id)).update({"status": status})
        elif table == "pending_companies":
            self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == int(item_id)).update({"status": status})
        self._session.commit()
        return True

    def count_pending(self, table: str = "pending_jobs") -> int:
        if table == "pending_jobs":
            return self._session.query(PendingJobModel).filter(PendingJobModel.status != "done").count()
        elif table == "pending_companies":
            return self._session.query(PendingCompanyModel).filter(PendingCompanyModel.status != "done").count()
        return 0
