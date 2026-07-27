"""SQLAlchemy-based company link repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from domain.repositories.company_link_repository import ICompanyLinkRepository
from infrastructure.database.models.company_model import CompanyLinkModel


class SQLAlchemyCompanyLinkRepository(ICompanyLinkRepository):
    """SQLAlchemy implementation of company link repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: CompanyLinkModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "company_id": m.company_id,
            "url": m.url,
            "title": m.title,
            "description": m.description,
            "status": m.status,
            "extracted_content": m.extracted_content,
            "created_at": m.created_at,
        }

    def get_by_company_id(self, company_id: int) -> list[dict[str, Any]]:
        rows = self._session.query(CompanyLinkModel).filter(
            CompanyLinkModel.company_id == company_id
        ).all()
        return [self._to_dict(r) for r in rows]

    def get_by_id(self, link_id: int) -> dict[str, Any] | None:
        m = self._session.query(CompanyLinkModel).filter(CompanyLinkModel.id == link_id).first()
        return self._to_dict(m) if m else None

    def create(self, company_id: int, url: str, title: str = "", description: str = "") -> dict[str, Any]:
        m = CompanyLinkModel(
            company_id=company_id,
            url=url,
            title=title,
            description=description,
            status="pending",
        )
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def delete(self, link_id: int, company_id: int) -> bool:
        m = self._session.query(CompanyLinkModel).filter(
            CompanyLinkModel.id == link_id,
            CompanyLinkModel.company_id == company_id,
        ).first()
        if not m:
            return False
        self._session.delete(m)
        self._session.commit()
        return True

    def reset_statuses(self, company_id: int) -> int:
        count = self._session.query(CompanyLinkModel).filter(
            CompanyLinkModel.company_id == company_id
        ).update({"status": "pending", "extracted_content": ""})
        self._session.commit()
        return count

    def update_status(self, link_id: int, status: str, extracted_content: str = "") -> bool:
        m = self._session.query(CompanyLinkModel).filter(CompanyLinkModel.id == link_id).first()
        if not m:
            return False
        m.status = status
        if extracted_content:
            m.extracted_content = extracted_content
        self._session.commit()
        return True
