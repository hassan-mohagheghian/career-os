"""Domain events for the Skills bounded context.

Emitted as the skill taxonomy evolves: categories created/deleted, a skill's
category set changed, composite skills broken down, and an alias promoted to
canonical. See `docs/domain/skills/events.md` for the catalog.
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


@dataclass(frozen=True)
class SkillBrokenDown(DomainEvent):
    """A composite skill was broken into atomic children."""

    skill_id: int | None = None
    skill_name: str = ""
    children: tuple[str, ...] = ()
    event_type: str = "skill.breakdown.created"


@dataclass(frozen=True)
class SkillCanonicalChanged(DomainEvent):
    """An alias was promoted to become the canonical name of a skill."""

    skill_id: int | None = None
    previous_name: str = ""
    new_name: str = ""
    event_type: str = "skill.canonical.changed"


__all__ = [
    "SkillCategoryCreated",
    "SkillCategoryDeleted",
    "SkillCategoriesChanged",
    "SkillBrokenDown",
    "SkillCanonicalChanged",
]
