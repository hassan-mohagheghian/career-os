"""SQLAlchemy-based pending companies repository (backed by CompanyModel)."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.domain.repositories.pending_repository import IPendingRepository
from companies.infrastructure.models.company_model import CompanyModel
from companies.infrastructure.mappers import company_model_to_dict


class SQLAlchemyPendingCompanyRepository(IPendingRepository):
    """SQLAlchemy implementation of the pending company intake queue."""

    def __init__(self, session: Session):
        self._session = session

    EXCLUDED_STATUSES = {"processed"}

    def list_pending(self, table: str = "pending_companies") -> list[dict[str, Any]]:
        rows = self._session.query(CompanyModel).filter(
            ~CompanyModel.status.in_(self.EXCLUDED_STATUSES)
        ).order_by(CompanyModel.created_at.desc()).all()
        return [company_model_to_dict(r) for r in rows]

    def get_by_id(self, item_id: str, table: str = "pending_companies") -> dict[str, Any] | None:
        model = self._session.query(CompanyModel).filter(CompanyModel.id == item_id).first()
        return company_model_to_dict(model) if model else None

    def create(self, data: dict[str, Any], table: str = "pending_companies") -> dict[str, Any]:
        model = CompanyModel(
            notes=json.dumps(data.get("notes", []), ensure_ascii=False) if data.get("notes") else "[]",
            source=data.get("source", "api"),
            status="created",
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return company_model_to_dict(model)

    def update_status(self, item_id: str, status: str, table: str = "pending_companies", **fields) -> bool:
        m = self._session.query(CompanyModel).filter(CompanyModel.id == item_id).first()
        if not m:
            return False
        m.status = status
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()
        return True

    def count_pending(self, table: str = "pending_companies") -> int:
        return self._session.query(CompanyModel).filter(
            ~CompanyModel.status.in_(self.EXCLUDED_STATUSES)
        ).count()

    def update_fields(self, item_id: str, table: str = "pending_companies", **fields) -> bool:
        m = self._session.query(CompanyModel).filter(CompanyModel.id == item_id).first()
        if not m:
            return False
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()
        return True

    def update_step(self, item_id: str, step_field: str, value: int, table: str = "pending_companies", **extra) -> bool:
        fields = {step_field: value}
        fields.update(extra)
        return self.update_fields(item_id, table, **fields)

    def save_session_id(self, item_id: str, session_id: str, table: str = "pending_companies") -> bool:
        return self.update_fields(item_id, table, session_id=session_id)

    def update_workflow_log(self, item_id: str, log_json: str, table: str = "pending_companies") -> bool:
        return self.update_fields(item_id, table, workflow_log=log_json)

    def get_max_queue_order(self, table: str = "pending_companies") -> int:
        result = self._session.query(func.max(CompanyModel.queue_order)).scalar()
        return result or 0

    ACTIVE_STATUSES = {'processing'}

    def get_processing_count(self, table: str = "pending_companies") -> int:
        return self._session.query(CompanyModel).filter(
            CompanyModel.status.in_(self.ACTIVE_STATUSES)
        ).count()

    def get_pending_count(self, table: str = "pending_companies") -> int:
        return self._session.query(CompanyModel).filter(
            CompanyModel.status == 'pending'
        ).count()

    def get_queued_count(self, table: str = "pending_companies") -> int:
        return self._session.query(CompanyModel).filter(
            CompanyModel.status == "queued"
        ).count()

    def get_processing_items(self, table: str = "pending_companies") -> list[dict[str, Any]]:
        rows = self._session.query(CompanyModel).filter(
            CompanyModel.status.in_(self.ACTIVE_STATUSES)
        ).all()
        return [company_model_to_dict(r) for r in rows]

    def mark_processing_as_waiting(self, table: str = "pending_companies") -> int:
        count = self._session.query(CompanyModel).filter(
            CompanyModel.status.in_(self.ACTIVE_STATUSES)
        ).update({"status": "pending"})
        self._session.commit()
        return count

    def reset_processing_orphans(self, table: str = "pending_companies") -> int:
        count = self._session.query(CompanyModel).filter(
            CompanyModel.status.in_(self.ACTIVE_STATUSES)
        ).update({"status": "created"})
        self._session.commit()
        return count

    def pick_queued_item(self, table: str = "pending_companies") -> dict[str, Any] | None:
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

    def get_queued_items(self, table: str = "pending_companies") -> list[dict[str, Any]]:
        rows = self._session.query(CompanyModel).filter(
            CompanyModel.status == "queued"
        ).order_by(CompanyModel.id.asc()).all()
        return [company_model_to_dict(r) for r in rows]

    def reset_steps(self, item_id: str, version: int, table: str = "pending_companies", keep_status: bool = False) -> bool:
        updates = {
            "error": None,
            "workflow_log": "[]",
            "current_node": None,
            "retry_count": 0,
            "failure_reason": None,
        }
        if not keep_status:
            updates["status"] = "created"
        self._session.query(CompanyModel).filter(CompanyModel.id == item_id).update(updates)
        self._session.commit()
        return True

    def get_all_for_stream(self, table: str = "pending_companies") -> list[dict[str, Any]]:
        rows = self._session.query(CompanyModel).order_by(CompanyModel.created_at.desc()).all()
        return [company_model_to_dict(r) for r in rows]

    def delete(self, item_id: str, table: str = "pending_companies") -> bool:
        m = self._session.query(CompanyModel).filter(CompanyModel.id == item_id).first()
        if m:
            self._session.delete(m)
            self._session.commit()
            return True
        return False

    def create_pending_company(self, input_text: str, input_type: str, source: str, status: str = "created", notes: str = "[]", company_id: str = None, links: str = "[]", name: str = None) -> dict[str, Any]:
        model = CompanyModel(
            name=name,
            notes=notes,
            source=source,
            status=status,
            input_text=input_text,
            input_type=input_type,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return company_model_to_dict(model)
