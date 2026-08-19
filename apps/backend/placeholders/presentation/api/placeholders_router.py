"""Placeholders API router.

GET /placeholders  — list the canonical keys and any saved values.
PUT /placeholders  — upsert a flat ``{key: value}`` map of placeholder values.

Owned by the Placeholders bounded context (per-context router, rule 10).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import get_placeholder_service
from placeholders.application.services.placeholder_service import PlaceholderService
from placeholders.domain.entities.placeholder import PlaceholderKey
from placeholders.presentation.api.schemas.placeholders import (
    PlaceholdersListResponse,
    PlaceholdersUpdateRequest,
    PlaceholdersUpdateResponse,
    build_list_response,
)

router = APIRouter()


@router.get("", response_model=PlaceholdersListResponse)
def list_placeholders(
    service: PlaceholderService = Depends(get_placeholder_service),
):
    items = service.list()
    return build_list_response(items, service.keys(), PlaceholderKey.LABELS)


@router.put("", response_model=PlaceholdersUpdateResponse)
def update_placeholders(
    body: PlaceholdersUpdateRequest,
    service: PlaceholderService = Depends(get_placeholder_service),
):
    stored = service.upsert_many(body.root)
    return PlaceholdersUpdateResponse(items=stored)


__all__ = ["router"]