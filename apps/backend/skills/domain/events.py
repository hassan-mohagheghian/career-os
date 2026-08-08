"""Domain events for the Skills bounded context.

Emitted as the skill taxonomy evolves: categories created/deleted and a skill's
category set changed. See `docs/domain/skills/events.md` for the catalog.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class SkillCategoryCreated(DomainEvent):
    """A category was added to the catalog."""

    name: str = ""
    event_type: str = "skill.category.created"


@dataclass(frozen=True)
class SkillCategoryDeleted(DomainEvent):
    """An unused category was removed from the catalog."""

    name: str = ""
    event_type: str = "skill.category.deleted"


@dataclass(frozen=True)
class SkillCategoriesChanged(DomainEvent):
    """A skill's category set changed (created/updated/categorized)."""

    skill_id: int | None = None
    skill_name: str = ""
    categories: tuple[str, ...] = ()
    event_type: str = "skill.categories.changed"


__all__ = [
    "SkillCategoryCreated",
    "SkillCategoryDeleted",
    "SkillCategoriesChanged",
]
