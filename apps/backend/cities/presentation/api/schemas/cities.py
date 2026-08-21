"""Pydantic schemas for the Cities API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CityListItemSchema(BaseModel):
    """A single city in the cities list."""

    id: str
    city: str
    country: str
    original_text: str | None = None
    address: str | None = None
    aliases: list[str] = Field(default_factory=list)
    job_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class CityListResponseSchema(BaseModel):
    """Cursor-paginated cities list response."""

    items: list[CityListItemSchema] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False
    total_items: int = 0


def build_city_list_response(
    items: list[dict[str, Any]],
    next_cursor: str | None,
    has_more: bool,
    total_items: int,
) -> CityListResponseSchema:
    return CityListResponseSchema(
        items=[CityListItemSchema(**i) for i in items],
        next_cursor=next_cursor,
        has_more=has_more,
        total_items=total_items,
    )


class CityMergeSchema(BaseModel):
    """Merge one or more source cities into a target city."""

    target_id: str
    source_ids: list[str] = Field(default_factory=list)


class CityAliasAddSchema(BaseModel):
    """Add an alias to a city."""

    alias_name: str


class CityCanonicalChangeSchema(BaseModel):
    """Promote an alias to be the canonical city name."""

    alias_name: str


__all__ = [
    "CityListItemSchema",
    "CityListResponseSchema",
    "build_city_list_response",
    "CityMergeSchema",
    "CityAliasAddSchema",
    "CityCanonicalChangeSchema",
]