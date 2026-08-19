"""SQLAlchemy implementation of the Placeholders repository."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from placeholders.domain.repositories.placeholder_repository import IPlaceholderRepository
from placeholders.infrastructure.mappers import placeholder_model_to_dict
from placeholders.infrastructure.models.placeholder_model import PlaceholderModel


class SQLAlchemyPlaceholderRepository(IPlaceholderRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_all(self) -> list[dict[str, Any]]:
        rows = self._session.scalars(
            select(PlaceholderModel).order_by(PlaceholderModel.key)
        ).all()
        return [placeholder_model_to_dict(r) for r in rows]

    def get_by_key(self, key: str) -> dict[str, Any] | None:
        model = self._session.get(PlaceholderModel, key)
        return placeholder_model_to_dict(model) if model else None

    def upsert(self, key: str, value: str) -> dict[str, Any]:
        model = self._session.get(PlaceholderModel, key)
        now = datetime.now(UTC).isoformat()
        if model is None:
            model = PlaceholderModel(key=key, value=value, updated_at=now)
            self._session.add(model)
        else:
            model.value = value
            model.updated_at = now
        self._session.flush()
        return placeholder_model_to_dict(model)


__all__ = ["SQLAlchemyPlaceholderRepository"]