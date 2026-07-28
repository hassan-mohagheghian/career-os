"""SQLAlchemy-based career insight repository implementation."""

from typing import Any

import json
from sqlalchemy.orm import Session

from career.domain.repositories.career_insight_repository import ICareerInsightRepository
from career.infrastructure.models.insight_model import CareerInsightModel


class SQLAlchemyCareerInsightRepository(ICareerInsightRepository):
    """SQLAlchemy implementation of career insight repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: CareerInsightModel) -> dict[str, Any]:
        data = {}
        if m.data_json:
            try:
                data = json.loads(m.data_json)
            except (json.JSONDecodeError, TypeError):
                data = {}
        return {
            "id": m.id,
            "insight_type": m.insight_type,
            "version": m.version,
            "score": m.score,
            "summary": m.summary,
            "data_json": data,
            "created_at": m.created_at,
        }

    def get_all(self) -> dict[str, Any]:
        rows = self._session.query(CareerInsightModel).order_by(CareerInsightModel.id.desc()).all()
        result = {}
        for row in rows:
            result[row.insight_type] = self._to_dict(row)
        return result

    def get_section(self, section: str) -> dict[str, Any] | None:
        m = self._session.query(CareerInsightModel).filter(
            CareerInsightModel.insight_type == section
        ).first()
        return self._to_dict(m) if m else None

    def upsert(self, section: str, data: dict[str, Any], version: int = 1, score: float | None = None, summary: str | None = None) -> None:
        existing = self._session.query(CareerInsightModel).filter(
            CareerInsightModel.insight_type == section
        ).first()
        data_json = json.dumps(data, ensure_ascii=False)
        if existing:
            existing.data_json = data_json
            if score is not None:
                existing.score = score
            if summary is not None:
                existing.summary = summary
        else:
            m = CareerInsightModel(
                insight_type=section,
                version=version,
                score=score,
                summary=summary,
                data_json=data_json,
            )
            self._session.add(m)
        self._session.commit()

    def delete_all(self) -> int:
        count = self._session.query(CareerInsightModel).delete()
        self._session.commit()
        return count
