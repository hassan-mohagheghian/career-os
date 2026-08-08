"""Skill repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISkillRepository(ABC):
    """Interface for skill data access."""

    @abstractmethod
    def list_visible(self, category: str = "") -> list[dict[str, Any]]:
        """Get visible skills with aliases."""
        ...

    @abstractmethod
    def list_hidden(self) -> list[dict[str, Any]]:
        """Get all hidden skills."""
        ...

    @abstractmethod
    def get_by_id(self, skill_id: int) -> dict[str, Any] | None:
        """Get a skill by ID."""
        ...

    @abstractmethod
    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Get a skill by name."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new skill."""
        ...

    @abstractmethod
    def update(self, skill_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a skill."""
        ...

    @abstractmethod
    def delete(self, skill_id: int) -> bool:
        """Delete a skill and its aliases."""
        ...

    @abstractmethod
    def set_hidden(self, skill_id: int, hidden: int) -> dict[str, Any] | None:
        """Set hidden flag on a skill."""
        ...

    @abstractmethod
    def set_pinned(self, skill_id: int, pinned: bool) -> dict[str, Any] | None:
        """Pin or unpin a skill."""
        ...

    @abstractmethod
    def rename(self, skill_id: int, new_name: str) -> dict[str, Any] | None:
        """Rename a skill and update all references."""
        ...

    @abstractmethod
    def merge(self, target_id: int, source_ids: list[int]) -> dict[str, Any]:
        """Merge source skills into target."""
        ...

    @abstractmethod
    def get_categories(self) -> list[dict[str, Any]]:
        """Get all categories in the catalog with per-category counts."""
        ...

    @abstractmethod
    def create_category(self, name: str) -> dict[str, Any] | None:
        """Add a category to the catalog. Returns None for blank names.

        Result: ``{"id", "name", "created": bool}`` — ``created`` is False when
        the category already exists.
        """
        ...

    @abstractmethod
    def delete_category(self, name: str) -> dict[str, Any]:
        """Remove an unused category.

        Result: ``{"status": "deleted"}``, ``{"status": "in_use", "count": n}``
        or ``{"status": "not_found"}``.
        """
        ...

    @abstractmethod
    def set_categories(self, skill_id: int, categories: list[str]) -> dict[str, Any] | None:
        """Replace a skill's categories and keep the primary column in sync."""
        ...

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get overall skill statistics."""
        ...

    @abstractmethod
    def bulk_hide(self, skill_ids: list[int]) -> int:
        """Hide multiple skills. Returns count hidden."""
        ...

    @abstractmethod
    def bulk_categorize(self, skill_ids: list[int], category: str) -> int:
        """Categorize multiple skills. Returns count updated."""
        ...

    @abstractmethod
    def get_relationships(self, skill_name: str) -> list[dict[str, Any]]:
        """Get all relationships for a skill."""
        ...

    @abstractmethod
    def create_relationship(self, data: dict[str, Any]) -> bool:
        """Create a skill relationship. Returns True if created."""
        ...

    @abstractmethod
    def delete_relationship(self, rel_id: int) -> bool:
        """Delete a skill relationship."""
        ...

    @abstractmethod
    def resolve_skill(self, data: dict[str, Any]) -> int:
        """Resolve a skill row by name (then alias), creating it when new.
        Returns the skill id."""
        ...

    @abstractmethod
    def upsert_mentions(self, skill_id: int, source_type: str, source_id: str, status: str = "", evidence: str = "[]") -> None:
        """Upsert a skill mention link for a job/company source."""
        ...

    @abstractmethod
    def delete_mentions_for_source(self, source_type: str, source_id: str) -> None:
        """Delete all mention links for a job/company source (idempotent reprocessing)."""
        ...

    @abstractmethod
    def get_mention_counts(self, skill_ids: list[int]) -> dict[int, int]:
        """Return {skill_id: total mention count} for the given skill ids.

        Each count sums the skill's own mentions plus mentions recorded under
        separate skill rows whose name matches one of the skill's aliases.
        """
        ...

    @abstractmethod
    def add_alias(self, skill_id: int, alias_name: str) -> dict[str, Any] | None:
        """Add an alias to a skill. Returns the updated skill or None."""
        ...

    @abstractmethod
    def remove_alias(self, skill_id: int, alias_name: str) -> dict[str, Any] | None:
        """Remove an alias from a skill. Returns the updated skill or None."""
        ...

    @abstractmethod
    def break_down(self, origin_id: int, child_names: list[str]) -> dict[str, Any]:
        """Break a composite skill into atomic children.

        Each child is resolved (name/alias/slug) and created only when missing.
        The origin's job mentions are duplicated onto every child and the
        origin is soft-hidden. Returns
        ``{"status", "origin": {...}, "children": [{"id", "name"}], "hidden": true}``
        or ``{"error": ...}``.
        """
        ...

    @abstractmethod
    def get_breakdown_map(self) -> list[dict[str, Any]]:
        """Return ``[{origin: {id, name}, children: [{id, name}, ...]}, ...]``
        for every composite skill with a recorded breakdown. Used to steer
        skill extraction."""
        ...

    @abstractmethod
    def list_breakdowns(self, skill_id: int) -> dict[str, Any]:
        """Return ``{"children": [...], "origin": {...} | None}`` for a skill."""
        ...

    @abstractmethod
    def promote_alias_to_canonical(self, skill_id: int, alias_name: str) -> dict[str, Any] | None:
        """Make an existing alias the canonical name of a skill.

        The previous canonical name becomes an alias. Returns the updated
        skill or None when the skill/alias is missing or the alias's slug
        collides with another skill's canonical slug.
        """
        ...

    @abstractmethod
    def normalize_all(self) -> dict[str, Any]:
        """Normalize every skill and category: recompute slugs, merge slug
        collisions (re-pointing mentions/category links and aliasing dupes).
        Returns a summary dict with counts."""
        ...
