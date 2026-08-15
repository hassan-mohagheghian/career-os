"""SQLAlchemy-based company repository implementation."""

import json
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from companies.domain.repositories.company_repository import ICompanyRepository
from companies.infrastructure.models.company_model import CompanyModel, CompanyIntelligenceModel
from companies.infrastructure.mappers import company_model_to_dict, company_intelligence_model_to_dict


class SQLAlchemyCompanyRepository(ICompanyRepository):
    """SQLAlchemy implementation of company repository."""

    def __init__(self, session: Session):
        self._session = session

    def list_all(self) -> list[dict[str, Any]]:
        rows = self._session.query(CompanyModel).filter(
            CompanyModel.name.isnot(None), CompanyModel.name != ''
        ).order_by(CompanyModel.name).all()
        return [company_model_to_dict(r) for r in rows]

    def get_by_id(self, company_id: str) -> dict[str, Any] | None:
        model = self._session.query(CompanyModel).filter(CompanyModel.id == company_id).first()
        if not model:
            return None
        return company_model_to_dict(model)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = CompanyModel(
            name=data.get("name"),
            industry=data.get("industry"),
            city=data.get("city"),
            country=data.get("country"),
            logo_url=data.get("logo_url"),
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def update(self, company_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = self._session.query(CompanyModel).filter(CompanyModel.id == company_id).first()
        if not model:
            return None

        for field in ["name", "industry", "city", "country", "logo_url", "description", "tech_stack", "website", "domain", "company_size", "company_type"]:
            if field in data:
                val = data[field]
                if isinstance(val, (list, dict)):
                    val = json.dumps(val)
                setattr(model, field, val)

        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def delete(self, company_id: str) -> bool:
        self._session.query(CompanyModel).filter(CompanyModel.id == company_id).delete()
        self._session.commit()
        return True

    def get_intelligence(self, company_id: str) -> dict[str, Any] | None:
        model = self._session.query(CompanyIntelligenceModel).filter(
            CompanyIntelligenceModel.company_id == company_id
        ).first()
        if not model:
            return None
        return company_intelligence_model_to_dict(model)

    # ── Extended methods for services ───────────────────────────────

    def insert(self, data: dict[str, Any]) -> dict[str, Any]:
        model = CompanyModel(**{k: v for k, v in data.items() if hasattr(CompanyModel, k)})
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def get_intelligence_by_company_id(self, company_id: str) -> dict[str, Any] | None:
        return self.get_intelligence(company_id)

    # ── Lifecycle methods ───────────────────────────────────────────

    ACTIVE_STATUSES = {'processing'}

    def get_pending_count(self) -> int:
        return self._session.query(CompanyModel).filter(
            CompanyModel.status == 'pending',
        ).count()

    def list_by_status(self, status: str) -> list[dict[str, Any]]:
        rows = self._session.query(CompanyModel).filter(
            CompanyModel.status == status,
        ).order_by(CompanyModel.created_at.desc()).all()
        return [company_model_to_dict(r) for r in rows]

    def get_processing_count(self) -> int:
        return self._session.query(CompanyModel).filter(
            CompanyModel.status.in_(self.ACTIVE_STATUSES),
        ).count()

    def get_queued_count(self) -> int:
        return self._session.query(CompanyModel).filter(
            CompanyModel.status == 'queued',
        ).count()

    def update_status(self, company_id: str, status: str, **extra: Any) -> bool:
        extra.setdefault("updated_at", datetime.now(UTC).isoformat())
        fields = {'status': status, **extra}
        self._session.query(CompanyModel).filter(CompanyModel.id == company_id).update(fields)
        self._session.commit()
        return True

    def pick_queued_item(self) -> dict[str, Any] | None:
        model = self._session.query(CompanyModel).filter(
            CompanyModel.status == 'queued',
        ).order_by(
            CompanyModel.id.asc(),
        ).first()
        if model:
            model.status = 'processing'
            model.updated_at = datetime.now(UTC).isoformat()
            self._session.commit()
            self._session.refresh(model)
            return company_model_to_dict(model)
        return None

    def get_processing_items(self) -> list[dict[str, Any]]:
        rows = self._session.query(CompanyModel).filter(
            CompanyModel.status.in_(self.ACTIVE_STATUSES),
        ).all()
        return [company_model_to_dict(r) for r in rows]

    def update_fields(self, company_id: str, **fields: Any) -> bool:
        fields.setdefault("updated_at", datetime.now(UTC).isoformat())
        self._session.query(CompanyModel).filter(CompanyModel.id == company_id).update(fields)
        self._session.commit()
        return True

    def list_for_matching(self) -> list[dict[str, Any]]:
        rows = self._session.query(
            CompanyModel.id,
            CompanyModel.name,
            CompanyModel.website,
            CompanyModel.domain,
            CompanyModel.parent_company_id,
        ).filter(
            CompanyModel.name.isnot(None),
            CompanyModel.name != '',
        ).all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "website": r.website,
                "domain": r.domain,
                "parent_company_id": r.parent_company_id,
            }
            for r in rows
        ]

    def count_aliases(self, company_id: str) -> int:
        return self._session.query(func.count(CompanyModel.id)).filter(
            CompanyModel.parent_company_id == company_id,
        ).scalar() or 0

    def get_total_count(self) -> int:
        return self._session.query(func.count(CompanyModel.id)).scalar() or 0

    def set_pinned(self, company_id: str, pinned: bool) -> bool:
        """Set or clear the pinned flag on a company. Returns True if the company exists."""
        model = self._session.query(CompanyModel).filter(CompanyModel.id == company_id).first()
        if not model:
            return False
        model.pinned = 1 if pinned else 0
        model.updated_at = datetime.now(UTC).isoformat()
        self._session.commit()
        return True

    def get_all_with_job_counts(self) -> list[dict[str, Any]]:
        from jobs.infrastructure.models.job_model import JobModel
        rows = self._session.query(
            CompanyModel,
            func.count(JobModel.id).label("job_count"),
        ).outerjoin(
            JobModel, (JobModel.company_id == CompanyModel.id) & (JobModel.deleted == 0)
        ).group_by(CompanyModel.id).order_by(CompanyModel.name).all()
        result = []
        for company, job_count in rows:
            d = company_model_to_dict(company)
            d["job_count"] = job_count
            result.append(d)
        return result

    def list_all_with_details(self) -> list[dict[str, Any]]:
        """All named companies with job counts and parsed intelligence scores.

        Returns each company dict augmented with ``job_count`` and ``_scores``
        (a parsed dict). Sort/pagination is applied by the v2 list use case.
        """
        from jobs.infrastructure.models.job_model import JobModel
        rows = self._session.query(
            CompanyModel,
            func.count(JobModel.id).label("job_count"),
            CompanyIntelligenceModel.scores,
        ).outerjoin(
            JobModel, (JobModel.company_id == CompanyModel.id) & (JobModel.deleted == 0)
        ).outerjoin(
            CompanyIntelligenceModel,
            CompanyIntelligenceModel.company_id == CompanyModel.id,
        ).filter(
            CompanyModel.name.isnot(None),
            CompanyModel.name != '',
        ).group_by(
            CompanyModel.id,
            CompanyIntelligenceModel.scores,
        ).all()

        result = []
        for company, job_count, scores_raw in rows:
            d = company_model_to_dict(company)
            d["job_count"] = job_count
            d["_scores"] = self._parse_scores(scores_raw)
            result.append(d)
        return result

    @staticmethod
    def _parse_scores(raw: Any) -> dict[str, Any]:
        """Parse the intelligence scores JSON (stored in a Text column)."""
        if not raw:
            return {}
        if isinstance(raw, dict):
            return raw
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}
