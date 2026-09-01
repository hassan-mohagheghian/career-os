from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy.orm import Session

from ...domain.entities.llm_configuration import LLMConfiguration
from ...domain.repositories.llm_configuration_repository import ILLMConfigurationRepository
from ..models.llm_configuration_model import LLMConfigurationModel


class SQLAlchemyLLMConfigurationRepository(ILLMConfigurationRepository):
    def __init__(self, session: Session, user_id: str = ""):
        self._session = session
        self._user_id = user_id

    def get_by_id(self, config_id: str) -> Optional[LLMConfiguration]:
        q = self._session.query(LLMConfigurationModel).filter(
            LLMConfigurationModel.id == config_id
        )
        if self._user_id:
            q = q.filter(LLMConfigurationModel.user_id == self._user_id)
        model = q.first()
        if not model:
            return None
        return self._to_entity(model)

    def get_all(self) -> list[LLMConfiguration]:
        q = self._session.query(LLMConfigurationModel)
        if self._user_id:
            q = q.filter(LLMConfigurationModel.user_id == self._user_id)
        models = q.order_by(LLMConfigurationModel.created_at.desc()).all()
        return [self._to_entity(m) for m in models]

    def save(self, config: LLMConfiguration) -> str:
        model = LLMConfigurationModel(
            id=config.id,
            name=config.name,
            model=config.model,
            model_version=config.model_version,
            enabled=config.enabled,
            created_at=config.created_at,
            updated_at=config.updated_at,
            user_id=self._user_id,
        )
        self._session.add(model)
        return config.id

    def update(self, config: LLMConfiguration) -> str:
        model = self._session.get(LLMConfigurationModel, config.id)
        if not model:
            return config.id
        model.name = config.name
        model.model = config.model
        model.model_version = config.model_version
        model.enabled = config.enabled
        model.updated_at = datetime.now(UTC)
        return config.id

    def delete(self, config_id: str) -> bool:
        model = self._session.get(LLMConfigurationModel, config_id)
        if not model:
            return False
        self._session.delete(model)
        return True

    def get_enabled(self) -> list[LLMConfiguration]:
        q = self._session.query(LLMConfigurationModel).filter_by(enabled=True)
        if self._user_id:
            q = q.filter(LLMConfigurationModel.user_id == self._user_id)
        models = q.order_by(LLMConfigurationModel.created_at.desc()).all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: LLMConfigurationModel) -> LLMConfiguration:
        return LLMConfiguration(
            id=model.id,
            name=model.name,
            model=model.model,
            model_version=model.model_version,
            enabled=model.enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
