"""Skill normalization service — application layer for break-down and
promote-to-canonical operations.

Owns the business rules for decomposing composite skills into atomic children
and for promoting an alias to the canonical name, and emits domain events for
the state changes it performs (AGENTS.md rule 16: events are emitted by the
service that performs the state change, never by callers). Emission is
best-effort via the injected ``SkillEventPublisher`` (in-memory collector
today, real transport later).
"""

from __future__ import annotations

from typing import Any

from skills.domain.repositories.skill_repository import ISkillRepository
from skills.domain.event_publisher import SkillEventPublisher
from skills.domain.events import SkillBrokenDown, SkillCanonicalChanged


class SkillNormalizationService:
    """Coordinates break-down and promote-to-canonical operations."""

    def __init__(
        self,
        repo: ISkillRepository,
        publisher: SkillEventPublisher,
    ):
        self._repo = repo
        self._publisher = publisher

    def break_down(self, origin_id: int, child_names: list[str]) -> dict[str, Any]:
        result = self._repo.break_down(origin_id, child_names)
        if "error" not in result:
            self._publisher.publish(SkillBrokenDown(
                aggregate_id=origin_id,
                skill_id=origin_id,
                skill_name=result.get("origin", {}).get("name", ""),
                children=tuple(c["name"] for c in result.get("children", [])),
            ))
        return result

    def promote_alias_to_canonical(self, skill_id: int, alias_name: str) -> dict[str, Any] | None:
        before = self._repo.get_by_id(skill_id)
        previous_name = (before or {}).get("name", "")
        result = self._repo.promote_alias_to_canonical(skill_id, alias_name)
        if result is not None:
            self._publisher.publish(SkillCanonicalChanged(
                aggregate_id=skill_id,
                skill_id=skill_id,
                previous_name=previous_name,
                new_name=alias_name,
            ))
        return result

    def get_breakdown_map(self) -> list[dict[str, Any]]:
        return self._repo.get_breakdown_map()

    def list_breakdowns(self, skill_id: int) -> dict[str, Any]:
        return self._repo.list_breakdowns(skill_id)
