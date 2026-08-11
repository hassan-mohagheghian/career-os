"""FollowUpService — adds, edits and deletes application follow-ups.

A follow-up carries a scheduled date, a note and a completion marker
(``completed_at``). Completing a follow-up sets ``completed_at``; un-completing
clears it. Domain events are emitted best-effort through the event publisher.
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from applications.domain.event_publisher import ApplicationEventPublisher, InMemoryEventCollector
from applications.domain.events import (
    ApplicationFollowUpAdded,
    ApplicationFollowUpDeleted,
    ApplicationFollowUpUpdated,
)
from shared.application.exceptions import NotFoundError, ValidationError


class FollowUpService:
    """Business operations for application follow-ups."""

    def __init__(
        self,
        follow_up_repo: Any,
        application_repo: Any,
        event_publisher: ApplicationEventPublisher | None = None,
    ):
        self._repo = follow_up_repo
        self._apps = application_repo
        self.event_publisher = event_publisher or InMemoryEventCollector()

    def add(self, application_id: str, scheduled_at: str | None, note: str) -> dict[str, Any]:
        self._ensure_application(application_id)
        if scheduled_at is not None and not str(scheduled_at).strip():
            scheduled_at = None
        now = datetime.now(UTC).isoformat()
        stored = self._repo.create(
            {
                "application_id": application_id,
                "scheduled_at": scheduled_at,
                "note": note or "",
                "completed_at": None,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._emit(
            ApplicationFollowUpAdded(
                aggregate_id=application_id,
                application_id=application_id,
                follow_up_id=stored["id"],
                scheduled_at=stored.get("scheduled_at"),
            )
        )
        return stored

    def update(
        self,
        follow_up_id: str,
        scheduled_at: str | None = None,
        note: str | None = None,
        completed: bool | None = None,
    ) -> dict[str, Any]:
        current = self._repo.get_by_id(follow_up_id)
        if not current:
            raise NotFoundError(f"Follow-up {follow_up_id} not found")

        update: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
        if scheduled_at is not None:
            update["scheduled_at"] = str(scheduled_at).strip() or None
        if note is not None:
            update["note"] = note
        if completed is not None:
            if completed and not current.get("completed_at"):
                update["completed_at"] = datetime.now(UTC).isoformat()
            elif not completed:
                update["completed_at"] = None

        stored = self._repo.update(follow_up_id, update) or current
        self._emit(
            ApplicationFollowUpUpdated(
                aggregate_id=current.get("application_id"),
                application_id=current.get("application_id") or "",
                follow_up_id=follow_up_id,
                completed=bool(stored.get("completed_at")),
            )
        )
        return stored

    def complete(self, follow_up_id: str, completed: bool = True) -> dict[str, Any]:
        return self.update(follow_up_id, completed=completed)

    def delete(self, follow_up_id: str) -> None:
        current = self._repo.get_by_id(follow_up_id)
        if not current:
            raise NotFoundError(f"Follow-up {follow_up_id} not found")
        self._repo.delete(follow_up_id)
        self._emit(
            ApplicationFollowUpDeleted(
                aggregate_id=current.get("application_id"),
                application_id=current.get("application_id") or "",
                follow_up_id=follow_up_id,
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


__all__ = ["FollowUpService"]
