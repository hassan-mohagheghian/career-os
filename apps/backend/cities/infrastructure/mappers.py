"""Domain-to-database mapping for the Cities context."""

from __future__ import annotations

from typing import Any

from cities.infrastructure.models.city_model import CityModel


def city_model_to_dict(
    model: CityModel,
    aliases: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": model.id,
        "city": model.city or "",
        "country": model.country or "",
        "original_text": model.original_text,
        "address": model.address,
        "hidden": bool(model.hidden),
        "aliases": aliases or [],
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


__all__ = ["city_model_to_dict"]