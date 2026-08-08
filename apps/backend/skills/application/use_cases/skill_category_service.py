"""Skill category service — application layer for category operations.

Owns the business rules around the dynamic category catalog and per-skill
category assignment, and emits domain events for the state changes it performs
(AGENTS.md rule 16b: events are emitted by the service that performs the state
change, never by callers). Emission is best-effort via the injected
``SkillEventPublisher`` (in-memory collector today, real transport later).
"""

from __future__ import annotations

from typing import Any

from skills.domain.repositories.skill_repository import ISkillRepository
from skills.domain.event_publisher import SkillEventPublisher
from skills.domain.events import (
    SkillCategoryCreated,
    SkillCategoryDeleted,
    SkillCategoriesChanged,
)


class SkillCategoryService:
    """Coordinates category catalog management and skill categorization."""

    def __init__(
        self,
        repo: ISkillRepository,
        publisher: SkillEventPublisher,
    ):
        self._repo = repo
        self._publisher = publisher

    def create_category(self, name: str) -> dict[str, Any]:
        result = self._repo.create_category(name)
        if result is not None and result.get("created"):
            self._publisher.publish(SkillCategoryCreated(
                aggregate_id=result["id"],
                name=result["name"],
            ))
        return result

    def delete_category(self, name: str) -> dict[str, Any]:
        result = self._repo.delete_category(name)
        if result.get("status") == "deleted":
            self._publisher.publish(SkillCategoryDeleted(name=name))
        return result

    def set_skill_categories(self, skill_id: int, categories: list[str]) -> dict[str, Any] | None:
        before = self._repo.get_by_id(skill_id)
        result = self._repo.set_categories(skill_id, categories)
        if result is not None:
            self._emit_if_changed(before, result)
        return result

    def categorize(self, skill_id: int, category: str) -> dict[str, Any] | None:
        return self.set_skill_categories(skill_id, [category])

    def bulk_categorize(self, skill_ids: list[int], category: str) -> int:
        for sid in skill_ids:
            before = self._repo.get_by_id(sid)
            result = self._repo.set_categories(sid, [category])
            if result is not None:
                self._emit_if_changed(before, result)
        return len(skill_ids)

    def update_skill(self, skill_id: int, updates: dict[str, Any]) -> dict[str, Any] | None:
        before = self._repo.get_by_id(skill_id)
        result = self._repo.update(skill_id, updates)
        if result is not None:
            self._emit_if_changed(before, result)
        return result

    def _emit_if_changed(self, before: dict[str, Any] | None, after: dict[str, Any]) -> None:
        before_cats = sorted((before or {}).get("categories", []))
        after_cats = sorted(after.get("categories", []))
        if before_cats == after_cats:
            return
        self._publisher.publish(SkillCategoriesChanged(
            aggregate_id=after.get("id"),
            skill_id=after.get("id"),
            skill_name=after.get("name", ""),
            categories=tuple(after.get("categories", [])),
        ))
