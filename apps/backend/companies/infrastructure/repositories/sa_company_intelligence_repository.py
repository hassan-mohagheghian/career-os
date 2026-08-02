"""SQLAlchemy-based company intelligence repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from companies.domain.repositories.company_intelligence_repository import ICompanyIntelligenceRepository
from companies.infrastructure.models.company_model import CompanyIntelligenceModel


class SQLAlchemyCompanyIntelligenceRepository(ICompanyIntelligenceRepository):
    """SQLAlchemy implementation of company intelligence repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: CompanyIntelligenceModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "company_id": m.company_id,
            "overview": m.overview,
            "culture_analysis": m.culture_analysis,
            "international_analysis": m.international_analysis,
            "career_analysis": m.career_analysis,
            "benefits_analysis": m.benefits_analysis,
            "visa_analysis": m.visa_analysis,
            "technology_analysis": m.technology_analysis,
            "recommendation": m.recommendation,
            "scores": m.scores,
            "raw_source_data": m.raw_source_data,
            "generated_at": m.generated_at,
        }

    def get_by_company_id(self, company_id: int) -> dict[str, Any] | None:
        m = self._session.query(CompanyIntelligenceModel).filter(
            CompanyIntelligenceModel.company_id == company_id
        ).first()
        return self._to_dict(m) if m else None

    def upsert(self, company_id: int, data: dict[str, Any]) -> dict[str, Any]:
        existing = self._session.query(CompanyIntelligenceModel).filter(
            CompanyIntelligenceModel.company_id == company_id
        ).first()
        if existing:
            for field in ["overview", "culture_analysis", "international_analysis", "career_analysis",
                          "benefits_analysis", "visa_analysis", "technology_analysis",
                          "recommendation", "scores", "raw_source_data"]:
                if field in data:
                    setattr(existing, field, data[field])
            self._session.commit()
            self._session.refresh(existing)
            return self._to_dict(existing)
        m = CompanyIntelligenceModel(company_id=company_id, **{k: v for k, v in data.items() if hasattr(CompanyIntelligenceModel, k)})
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def delete_by_company_id(self, company_id: int) -> bool:
        m = self._session.query(CompanyIntelligenceModel).filter(
            CompanyIntelligenceModel.company_id == company_id
        ).first()
        if not m:
            return False
        self._session.delete(m)
        self._session.commit()
        return True
