"""SQLAlchemy-based insight repository implementation."""

import json
from typing import Any

from sqlalchemy.orm import Session

from career.domain.repositories.insight_repository import IInsightRepository
from career.infrastructure.models.insight_model import CareerInsightModel, CareerInsightRunModel
from shared.infrastructure.database.mappers import career_insight_model_to_dict, career_insight_run_model_to_dict


class SQLAlchemyInsightRepository(IInsightRepository):
    """SQLAlchemy implementation of insight repository."""

    def __init__(self, session: Session):
        self._session = session

    def get_all(self) -> dict[str, Any]:
        rows = self._session.query(CareerInsightModel).order_by(CareerInsightModel.id.desc()).all()
        result = {}
        for row in rows:
            result[row.insight_type] = career_insight_model_to_dict(row)
        return result

    def get_section(self, section: str) -> dict[str, Any] | None:
        model = self._session.query(CareerInsightModel).filter(
            CareerInsightModel.insight_type == section
        ).first()
        if not model:
            return None
        return career_insight_model_to_dict(model)

    def get_statuses(self) -> list[dict[str, Any]]:
        result = []

        # Try to get statuses from career_insight_runs
        runs = self._session.query(CareerInsightRunModel).order_by(
            CareerInsightRunModel.id.desc()
        ).all()

        seen = set()
        for run in runs:
            if run.insight_type not in seen:
                seen.add(run.insight_type)
                result.append({
                    "section": run.insight_type,
                    "status": run.status or "idle",
                    "updated_at": run.completed_at or run.started_at,
                })

        # Add insight types that exist in career_insights but not in runs
        all_types = self._session.query(CareerInsightModel.insight_type).distinct().all()
        seen_sections = {r["section"] for r in result}
        for (insight_type,) in all_types:
            if insight_type not in seen_sections:
                result.append({
                    "section": insight_type,
                    "status": "completed",
                    "updated_at": None,
                })

        return result

    def upsert_section(self, section: str, data: dict[str, Any], status: str = "completed") -> None:
        existing = self._session.query(CareerInsightModel).filter(
            CareerInsightModel.insight_type == section
        ).first()

        data_json = json.dumps(data)

        if existing:
            existing.data_json = data_json
        else:
            model = CareerInsightModel(
                insight_type=section,
                data_json=data_json,
                version=1,
            )
            self._session.add(model)

        self._session.commit()
