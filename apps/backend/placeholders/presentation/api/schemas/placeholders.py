"""Pydantic schemas for the Placeholders API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, RootModel


class PlaceholderSchema(BaseModel):
    key: str
    value: str = ""
    updated_at: str | None = None


class PlaceholdersListResponse(BaseModel):
    keys: list[dict[str, str]] = []
    items: list[PlaceholderSchema] = []
    values: dict[str, str] = {}


class PlaceholdersUpdateRequest(RootModel[dict[str, str]]):
    """A flat ``{key: value}`` map of placeholder values to upsert."""

    root: dict[str, str]


class PlaceholdersUpdateResponse(BaseModel):
    items: list[PlaceholderSchema] = []


def build_list_response(
    items: list[dict[str, Any]],
    keys: list[str],
    labels: dict[str, str],
) -> PlaceholdersListResponse:
    return PlaceholdersListResponse(
        keys=[{"key": k, "label": labels.get(k, k)} for k in keys],
        items=[PlaceholderSchema(**i) for i in items],
        values={i["key"]: i["value"] or "" for i in items},
    )


__all__ = [
    "PlaceholderSchema",
    "PlaceholdersListResponse",
    "PlaceholdersUpdateRequest",
    "PlaceholdersUpdateResponse",
    "build_list_response",
]