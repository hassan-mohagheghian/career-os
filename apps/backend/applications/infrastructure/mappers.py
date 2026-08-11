"""Mappers between SQLAlchemy models and dict representations."""

from __future__ import annotations

import json
from typing import Any

from applications.infrastructure.models.application_model import (
    ApplicationDocumentModel,
    ApplicationFollowUpModel,
    ApplicationModel,
    ApplicationPreparationModel,
    _now_iso,
)


def _json_loads(value: Any) -> Any:
    if value is None:
        return {}
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


def application_model_to_dict(model: ApplicationModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "job_id": model.job_id,
        "status": model.status,
        "applied_at": model.applied_at,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_application_model(data: dict[str, Any]) -> ApplicationModel:
    return ApplicationModel(
        id=data.get("id"),
        job_id=data.get("job_id", ""),
        status=data.get("status", "recommended"),
        applied_at=data.get("applied_at"),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )


def follow_up_model_to_dict(model: ApplicationFollowUpModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "application_id": model.application_id,
        "scheduled_at": model.scheduled_at,
        "note": model.note,
        "completed_at": model.completed_at,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_follow_up_model(data: dict[str, Any]) -> ApplicationFollowUpModel:
    return ApplicationFollowUpModel(
        id=data.get("id"),
        application_id=data.get("application_id", ""),
        scheduled_at=data.get("scheduled_at"),
        note=data.get("note", ""),
        completed_at=data.get("completed_at"),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )


def document_model_to_dict(model: ApplicationDocumentModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "application_id": model.application_id,
        "document_type": model.document_type,
        "version": model.version,
        "content": model.content,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_document_model(data: dict[str, Any]) -> ApplicationDocumentModel:
    return ApplicationDocumentModel(
        id=data.get("id"),
        application_id=data.get("application_id", ""),
        document_type=data.get("document_type", ""),
        version=data.get("version", 1),
        content=data.get("content", ""),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )


def preparation_model_to_dict(model: ApplicationPreparationModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "application_id": model.application_id,
        "version": model.version,
        "payload": _json_loads(model.payload),
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_preparation_model(data: dict[str, Any]) -> ApplicationPreparationModel:
    payload = data.get("payload")
    return ApplicationPreparationModel(
        id=data.get("id"),
        application_id=data.get("application_id", ""),
        version=data.get("version", 1),
        payload=json.dumps(payload or {}, ensure_ascii=False),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )
