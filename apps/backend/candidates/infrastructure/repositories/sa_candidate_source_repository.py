"""SQLAlchemy implementation of the candidate source repository."""

from typing import Any

from sqlalchemy.orm import Session

from candidates.domain.repositories.candidate_source_repository import ICandidateSourceRepository
from candidates.infrastructure.models.candidate_model import CandidateSourceModel, _now_iso
from candidates.infrastructure.mappers import dict_to_source_model, source_model_to_dict


class SQLAlchemyCandidateSourceRepository(ICandidateSourceRepository):
    """SQLAlchemy implementation of the candidate source repository."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_source_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return source_model_to_dict(model)

    def list_for_profile(self, profile_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(CandidateSourceModel)
            .filter(CandidateSourceModel.profile_id == profile_id)
            .order_by(CandidateSourceModel.created_at.desc())
            .all()
        )
        return [source_model_to_dict(r) for r in rows]

    def get_by_type_and_version(self, profile_id: str, source_type: str, version: int) -> dict[str, Any] | None:
        model = (
            self._session.query(CandidateSourceModel)
            .filter(
                CandidateSourceModel.profile_id == profile_id,
                CandidateSourceModel.source_type == source_type,
                CandidateSourceModel.version == version,
            )
            .first()
        )
        return source_model_to_dict(model) if model else None

    def get_latest_by_type(self, profile_id: str, source_type: str) -> dict[str, Any] | None:
        model = (
            self._session.query(CandidateSourceModel)
            .filter(
                CandidateSourceModel.profile_id == profile_id,
                CandidateSourceModel.source_type == source_type,
            )
            .order_by(CandidateSourceModel.version.desc())
            .first()
        )
        return source_model_to_dict(model) if model else None

    def get_next_version(self, profile_id: str, source_type: str) -> int:
        latest = self.get_latest_by_type(profile_id, source_type)
        return int(latest.get("version") or 0) + 1 if latest else 1

    def has_unprocessed_sources(self, profile_id: str) -> bool:
        row = (
            self._session.query(CandidateSourceModel)
            .filter(
                CandidateSourceModel.profile_id == profile_id,
                CandidateSourceModel.status != "processed",
            )
            .first()
        )
        return row is not None

    def has_any_sources(self, profile_id: str) -> bool:
        row = (
            self._session.query(CandidateSourceModel)
            .filter(CandidateSourceModel.profile_id == profile_id)
            .first()
        )
        return row is not None

    def update(self, source_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = self._session.query(CandidateSourceModel).filter(CandidateSourceModel.id == source_id).first()
        if not model:
            return None
        for field in ["profile_id", "source_type", "version", "status", "error", "processed_at", "raw_text"]:
            if field in data:
                setattr(model, field, data[field])
        model.updated_at = _now_iso()
        self._session.commit()
        return source_model_to_dict(model)
