"""SQLAlchemy implementation of IGenerationSessionRepository."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from ...domain.entities.generation_session import GenerationSession
from ...domain.repositories.generation_session_repository import IGenerationSessionRepository
from ..models.generation_session_model import GenerationSessionModel


class SQLAlchemyGenerationSessionRepository(IGenerationSessionRepository):
    """SQLAlchemy implementation of the generation session repository."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    def get_by_id(self, session_id: str) -> Optional[GenerationSession]:
        with self._session_factory() as db:
            model = db.get(GenerationSessionModel, session_id)
            if not model:
                return None
            return self._to_entity(model)

    def save(self, session: GenerationSession) -> str:
        with self._session_factory() as db:
            model = db.get(GenerationSessionModel, session.id)
            if model:
                model.workflow_type = session.workflow_type
                model.status = session.status
                model.current_stage = session.current_stage
                model.progress = session.progress
                model.errors = json.dumps(session.errors)
                model.metadata_json = json.dumps(session.metadata)
                model.entity_type = session.entity_type
                model.entity_id = session.entity_id
                model.started_at = session.started_at
                model.completed_at = session.completed_at
                model.updated_at = datetime.utcnow()
            else:
                model = GenerationSessionModel(
                    id=session.id,
                    workflow_type=session.workflow_type,
                    status=session.status,
                    current_stage=session.current_stage,
                    progress=session.progress,
                    errors=json.dumps(session.errors),
                    metadata_json=json.dumps(session.metadata),
                    entity_type=session.entity_type,
                    entity_id=session.entity_id,
                    started_at=session.started_at,
                    completed_at=session.completed_at,
                )
                db.add(model)
            db.commit()
            return session.id

    def delete(self, session_id: str) -> bool:
        with self._session_factory() as db:
            model = db.get(GenerationSessionModel, session_id)
            if not model:
                return False
            db.delete(model)
            db.commit()
            return True

    def get_by_entity(self, entity_type: str, entity_id: str) -> list[GenerationSession]:
        with self._session_factory() as db:
            models = (
                db.query(GenerationSessionModel)
                .filter_by(entity_type=entity_type, entity_id=entity_id)
                .order_by(GenerationSessionModel.created_at.desc())
                .all()
            )
            return [self._to_entity(m) for m in models]

    def get_recent(self, limit: int = 10) -> list[GenerationSession]:
        with self._session_factory() as db:
            models = (
                db.query(GenerationSessionModel)
                .order_by(GenerationSessionModel.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._to_entity(m) for m in models]

    def _to_entity(self, model: GenerationSessionModel) -> GenerationSession:
        """Convert SQLAlchemy model to domain entity."""
        return GenerationSession(
            id=model.id,
            workflow_type=model.workflow_type,
            status=model.status,
            current_stage=model.current_stage,
            progress=model.progress,
            errors=json.loads(model.errors) if model.errors else [],
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
