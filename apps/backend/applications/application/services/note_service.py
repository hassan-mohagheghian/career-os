"""NoteService — adds and deletes free-text application notes.

A note is plain user-authored text (an activity log entry in the user's own
words) stamped with its creation time. Notes are immutable: there is no edit
operation. Domain events are emitted best-effort through the event publisher.
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from applications.domain.event_publisher import ApplicationEventPublisher, InMemoryEventCollector
from applications.domain.events import ApplicationNoteAdded, ApplicationNoteDeleted
from shared.application.exceptions import NotFoundError, ValidationError


class NoteService:
    """Business operations for application notes."""

    def __init__(
        self,
        note_repo: Any,
        application_repo: Any,
        event_publisher: ApplicationEventPublisher | None = None,
    ):
        self._repo = note_repo
        self._apps = application_repo
        self.event_publisher = event_publisher or InMemoryEventCollector()

    def add(self, application_id: str, content: str) -> dict[str, Any]:
        self._ensure_application(application_id)
        text = str(content or "").strip()
        if not text:
            raise ValidationError("Note content must not be empty")
        now = datetime.now(UTC).isoformat()
        stored = self._repo.create(
            {
                "application_id": application_id,
                "content": text,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._emit(
            ApplicationNoteAdded(
                aggregate_id=application_id,
                application_id=application_id,
                note_id=stored["id"],
            )
        )
        return stored

    def delete(self, note_id: str) -> None:
        current = self._repo.get_by_id(note_id)
        if not current:
            raise NotFoundError(f"Note {note_id} not found")
        self._repo.delete(note_id)
        self._emit(
            ApplicationNoteDeleted(
                aggregate_id=current.get("application_id"),
                application_id=current.get("application_id") or "",
                note_id=note_id,
            )
        )

    def _ensure_application(self, application_id: str) -> None:
        if not self._apps.get_by_id(application_id):
            raise NotFoundError(f"Application {application_id} not found")

    def _emit(self, event: Any) -> None:
        try:
            self.event_publisher.publish(event)
        except Exception:  # noqa: BLE001 — best-effort publishing
            pass


__all__ = ["NoteService"]
