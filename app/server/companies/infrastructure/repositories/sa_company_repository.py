"""SQLAlchemy-based company repository implementation."""

import json
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from companies.domain.repositories.company_repository import ICompanyRepository
from companies.infrastructure.models.company_model import CompanyModel, CompanyIntelligenceModel
from shared.infrastructure.database.mappers import company_model_to_dict, company_intelligence_model_to_dict


class SQLAlchemyCompanyRepository(ICompanyRepository):
    """SQLAlchemy implementation of company repository."""

    def __init__(self, session: Session):
        self._session = session

    def list_all(self) -> list[dict[str, Any]]:
        rows = self._session.query(CompanyModel).order_by(CompanyModel.name).all()
        return [company_model_to_dict(r) for r in rows]

    def get_by_id(self, company_id: int) -> dict[str, Any] | None:
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

    def update(self, company_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        model = self._session.query(CompanyModel).filter(CompanyModel.id == company_id).first()
        if not model:
            return None

        for field in ["name", "industry", "city", "country", "logo_url", "notes", "description", "tech_stack", "website", "domain", "company_size", "company_type"]:
            if field in data:
                val = data[field]
                if isinstance(val, (list, dict)):
                    val = json.dumps(val)
                setattr(model, field, val)

        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def delete(self, company_id: int) -> bool:
        self._session.query(CompanyModel).filter(CompanyModel.id == company_id).delete()
        self._session.commit()
        return True

    def get_intelligence(self, company_id: int) -> dict[str, Any] | None:
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

    def get_intelligence_by_company_id(self, company_id: int) -> dict[str, Any] | None:
        return self.get_intelligence(company_id)

    def get_total_count(self) -> int:
        return self._session.query(func.count(CompanyModel.id)).scalar() or 0

    def get_all_with_job_counts(self) -> list[dict[str, Any]]:
        from jobs.infrastructure.models.job_model import JobModel
        rows = self._session.query(
            CompanyModel,
            func.count(JobModel.num).label("job_count"),
        ).outerjoin(
            JobModel, (JobModel.company_id == CompanyModel.id) & (JobModel.deleted == 0)
        ).group_by(CompanyModel.id).order_by(CompanyModel.name).all()
        result = []
        for company, job_count in rows:
            d = company_model_to_dict(company)
            d["job_count"] = job_count
            result.append(d)
        return result
