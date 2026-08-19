"""Domain-to-database mapping for the Placeholders context."""

from __future__ import annotations

from typing import Any

from placeholders.infrastructure.models.placeholder_model import PlaceholderModel


def placeholder_model_to_dict(model: PlaceholderModel) -> dict[str, Any]:
    return {
        "key": model.key,
        "value": model.value or "",
        "updated_at": model.updated_at,
    }


__all__ = ["placeholder_model_to_dict"]