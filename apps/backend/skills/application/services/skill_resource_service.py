"""SkillResourceService — adds and deletes skill notes and links.

Notes are free-text activity entries (user's own words + creation time).
Links are titled resource URLs (documentation, tutorials, etc.).
Both are immutable (no edit, only add/delete).
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from shared.application.exceptions import NotFoundError, ValidationError


class SkillResourceService:
    """Business operations for skill notes and links."""

    def __init__(
        self,
        note_repo: Any,
        link_repo: Any,
        skill_repo: Any,
    ):
        self._notes = note_repo
        self._links = link_repo
        self._skills = skill_repo

    def add_note(self, skill_id: int, content: str) -> dict[str, Any]:
        self._ensure_skill(skill_id)
        text = str(content or "").strip()
        if not text:
            raise ValidationError("Note content must not be empty")
        now = datetime.now(UTC).isoformat()
        return self._notes.create(
            {
                "skill_id": skill_id,
                "content": text,
                "created_at": now,
                "updated_at": now,
            }
        )

    def delete_note(self, note_id: int) -> None:
        current = self._notes.get_by_id(note_id)
        if not current:
            raise NotFoundError(f"Note {note_id} not found")
        self._notes.delete(note_id)

    def add_link(self, skill_id: int, title: str, url: str) -> dict[str, Any]:
        self._ensure_skill(skill_id)
        t = str(title or "").strip()
        u = str(url or "").strip()
        if not t:
            raise ValidationError("Link title must not be empty")
        if not u:
            raise ValidationError("Link URL must not be empty")
        now = datetime.now(UTC).isoformat()
        return self._links.create(
            {
                "skill_id": skill_id,
                "title": t,
                "url": u,
                "created_at": now,
            }
        )

    def delete_link(self, link_id: int) -> None:
        current = self._links.get_by_id(link_id)
        if not current:
            raise NotFoundError(f"Link {link_id} not found")
        self._links.delete(link_id)

    def _ensure_skill(self, skill_id: int) -> None:
        if not self._skills.get_by_id(skill_id):
            raise NotFoundError(f"Skill {skill_id} not found")


__all__ = ["SkillResourceService"]
