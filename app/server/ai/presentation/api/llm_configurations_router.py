from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dependencies import get_session
from shared.application.exceptions import NotFoundError, ConflictError
from ai.infrastructure.repositories.llm_configuration_repository import SQLAlchemyLLMConfigurationRepository
from ai.domain.entities.llm_configuration import LLMConfiguration
from ..schemas.llm_configuration_schemas import (
    CreateLLMConfigurationRequest,
    UpdateLLMConfigurationRequest,
    LLMConfigurationResponse,
    CreateLLMConfigurationResponse,
)

router = APIRouter()


def get_repo(session: Session = Depends(get_session)):
    return SQLAlchemyLLMConfigurationRepository(session)


@router.get("", response_model=list[LLMConfigurationResponse])
def list_configurations(repo: SQLAlchemyLLMConfigurationRepository = Depends(get_repo)):
    configs = repo.get_all()
    return [_entity_to_response(c) for c in configs]


@router.get("/{config_id}", response_model=LLMConfigurationResponse)
def get_configuration(config_id: str, repo: SQLAlchemyLLMConfigurationRepository = Depends(get_repo)):
    config = repo.get_by_id(config_id)
    if not config:
        raise NotFoundError(detail="Configuration not found")
    return _entity_to_response(config)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateLLMConfigurationResponse)
def create_configuration(body: CreateLLMConfigurationRequest, repo: SQLAlchemyLLMConfigurationRepository = Depends(get_repo)):
    existing = repo.get_all()
    for c in existing:
        if c.name == body.name:
            raise ConflictError(detail="Configuration name already exists")
    config = LLMConfiguration(
        id=str(uuid4()),
        name=body.name,
        model=body.model,
        model_version=body.model_version,
        enabled=body.enabled,
    )
    config_id = repo.save(config)
    return CreateLLMConfigurationResponse(id=config_id)


@router.patch("/{config_id}", response_model=LLMConfigurationResponse)
def update_configuration(config_id: str, body: UpdateLLMConfigurationRequest, repo: SQLAlchemyLLMConfigurationRepository = Depends(get_repo)):
    config = repo.get_by_id(config_id)
    if not config:
        raise NotFoundError(detail="Configuration not found")

    if body.name is not None and body.name != config.name:
        existing = repo.get_all()
        for c in existing:
            if c.name == body.name and c.id != config_id:
                raise ConflictError(detail="Configuration name already exists")

    config.update(
        name=body.name,
        model=body.model,
        model_version=body.model_version,
        enabled=body.enabled,
    )
    repo.update(config)
    return _entity_to_response(config)


@router.delete("/{config_id}")
def delete_configuration(config_id: str, repo: SQLAlchemyLLMConfigurationRepository = Depends(get_repo)):
    config = repo.get_by_id(config_id)
    if not config:
        raise NotFoundError(detail="Configuration not found")
    repo.delete(config_id)
    return {"status": "deleted"}


@router.post("/{config_id}/enable", response_model=LLMConfigurationResponse)
def enable_configuration(config_id: str, repo: SQLAlchemyLLMConfigurationRepository = Depends(get_repo)):
    config = repo.get_by_id(config_id)
    if not config:
        raise NotFoundError(detail="Configuration not found")
    config.enable()
    repo.update(config)
    return _entity_to_response(config)


@router.post("/{config_id}/disable", response_model=LLMConfigurationResponse)
def disable_configuration(config_id: str, repo: SQLAlchemyLLMConfigurationRepository = Depends(get_repo)):
    config = repo.get_by_id(config_id)
    if not config:
        raise NotFoundError(detail="Configuration not found")
    config.disable()
    repo.update(config)
    return _entity_to_response(config)


def _entity_to_response(config: LLMConfiguration) -> LLMConfigurationResponse:
    return LLMConfigurationResponse(
        id=config.id,
        name=config.name,
        model=config.model,
        model_version=config.model_version,
        enabled=config.enabled,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )
