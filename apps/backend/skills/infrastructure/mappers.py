"""Domain-to-database mapping for the Skills context.

Converts between domain dictionaries and SQLAlchemy ORM models in the
infrastructure layer, keeping the domain layer clean of persistence concerns.
"""

import json
from typing import Any
from datetime import datetime

from skills.infrastructure.models.skill_model import SkillModel, SkillNoteModel, SkillLinkModel


def _to_str(value: Any) -> Any:
    """Normalize datetime values to ISO strings (Text columns may hold datetimes on fresh inserts)."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def skill_model_to_dict(
    model: SkillModel,
    aliases: list[str] | None = None,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """Convert a SkillModel to a domain dictionary."""
    result = {
        "id": model.id,
        "name": model.name,
        "slug": model.slug,
        "level": model.level,
        "roles": model.roles,
        "path": model.path,
        "source": model.source,
        "hidden": model.hidden,
        "pinned": bool(model.pinned),
        "merged_into": model.merged_into,
        "category": model.category,
        "categories": list(categories) if categories is not None else [],
        "confidence": model.confidence,
        "market_relevance": model.market_relevance,
        "evidence": model.evidence,
        "source_type": model.source_type,
        "tags": json.loads(model.tags) if model.tags else [],
        "created_at": _to_str(model.created_at),
    }
    if aliases is not None:
        result["aliases"] = aliases
    return result


def dict_to_skill_model(data: dict[str, Any]) -> SkillModel:
    """Convert a domain dictionary to a SkillModel."""
    skill_data = {}
    for k, v in data.items():
        if hasattr(SkillModel, k):
            if k == "tags" and isinstance(v, list):
                skill_data[k] = json.dumps(v)
            else:
                skill_data[k] = v
    return SkillModel(**skill_data)


def skill_note_model_to_dict(model: SkillNoteModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "skill_id": model.skill_id,
        "content": model.content,
        "created_at": _to_str(model.created_at),
        "updated_at": _to_str(model.updated_at),
    }


def dict_to_skill_note_model(data: dict[str, Any]) -> SkillNoteModel:
    now = datetime.utcnow().isoformat()
    return SkillNoteModel(
        id=data.get("id"),
        skill_id=data.get("skill_id", 0),
        content=data.get("content", ""),
        created_at=data.get("created_at") or now,
        updated_at=data.get("updated_at") or now,
    )


def skill_link_model_to_dict(model: SkillLinkModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "skill_id": model.skill_id,
        "title": model.title,
        "url": model.url,
        "created_at": _to_str(model.created_at),
    }


def dict_to_skill_link_model(data: dict[str, Any]) -> SkillLinkModel:
    now = datetime.utcnow().isoformat()
    return SkillLinkModel(
        id=data.get("id"),
        skill_id=data.get("skill_id", 0),
        title=data.get("title", ""),
        url=data.get("url", ""),
        created_at=data.get("created_at") or now,
    )
