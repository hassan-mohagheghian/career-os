"""Mappers between SQLAlchemy models and dict representations."""

from __future__ import annotations

import json
from typing import Any

from applications.infrastructure.models.application_model import (
    ApplicationDocumentModel,
    ApplicationFollowUpModel,
    ApplicationModel,
    ApplicationNoteModel,
    ApplicationStatusEventModel,
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
        status=data.get("status", "seen"),
        applied_at=data.get("applied_at"),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
        user_id=data.get("user_id", ""),
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


def note_model_to_dict(model: ApplicationNoteModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "application_id": model.application_id,
        "content": model.content,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_note_model(data: dict[str, Any]) -> ApplicationNoteModel:
    return ApplicationNoteModel(
        id=data.get("id"),
        application_id=data.get("application_id", ""),
        content=data.get("content", ""),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )


def status_event_model_to_dict(model: ApplicationStatusEventModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "application_id": model.application_id,
        "status": model.status,
        "changed_at": model.changed_at,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_status_event_model(data: dict[str, Any]) -> ApplicationStatusEventModel:
    return ApplicationStatusEventModel(
        id=data.get("id"),
        application_id=data.get("application_id", ""),
        status=data.get("status", ""),
        changed_at=data.get("changed_at"),
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
