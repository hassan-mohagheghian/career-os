"""SQLAlchemy implementation of the candidate repository."""

from typing import Any

from sqlalchemy.orm import Session

from candidates.domain.repositories.candidate_repository import ICandidateRepository
from candidates.infrastructure.models.candidate_model import CandidateModel, _now_iso
from candidates.infrastructure.mappers import candidate_model_to_dict, dict_to_candidate_model


class SQLAlchemyCandidateRepository(ICandidateRepository):
    """SQLAlchemy implementation of the candidate repository."""

    def __init__(self, session: Session):
        self._session = session

    def get_candidate(self) -> dict[str, Any] | None:
        model = (
            self._session.query(CandidateModel)
            .order_by(CandidateModel.created_at.asc())
            .first()
        )
        return candidate_model_to_dict(model) if model else None

    def create_candidate(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_candidate_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return candidate_model_to_dict(model)

    def update_candidate(self, candidate_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = self._session.query(CandidateModel).filter(CandidateModel.id == candidate_id).first()
        if not model:
            return None
        for field in ["name", "headline", "summary", "location"]:
            if field in data:
                setattr(model, field, data[field])
        model.updated_at = _now_iso()
        self._session.commit()
        return candidate_model_to_dict(model)
