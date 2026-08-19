"""StatusEventService — edits application status-timeline entries.

A timeline entry records that an application entered a status at ``changed_at``.
Entries are created automatically when an application is created or its status
changes (defaulting the time to *now*); this service lets the user correct the
recorded time afterwards. Domain events are emitted best-effort through the
event publisher.
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from applications.domain.entities.application import ApplicationStatus
from applications.domain.event_publisher import ApplicationEventPublisher, InMemoryEventCollector
from applications.domain.events import ApplicationStatusChanged, ApplicationStatusRemoved
from shared.application.exceptions import NotFoundError, ValidationError


class StatusEventService:
    """Business operations for application status-timeline entries."""

    def __init__(
        self,
        status_event_repo: Any,
        application_repo: Any = None,
        event_publisher: ApplicationEventPublisher | None = None,
    ):
        self._repo = status_event_repo
        self._application_repo = application_repo
        self.event_publisher = event_publisher or InMemoryEventCollector()

    def update_changed_at(self, event_id: str, changed_at: str) -> dict[str, Any]:
        """Set the recorded time for a status event."""
        current = self._repo.get_by_id(event_id)
        if not current:
            raise NotFoundError(f"Status event {event_id} not found")

        stored = self._repo.update(
            event_id,
            {
                "changed_at": changed_at or None,
                "updated_at": datetime.now(UTC).isoformat(),
            },
        ) or current
        self._emit(
            ApplicationStatusChanged(
                aggregate_id=current.get("application_id"),
                application_id=current.get("application_id") or "",
                status=current.get("status") or "",
                changed_at=stored.get("changed_at"),
            )
        )
        return stored

    def delete(self, event_id: str) -> None:
        """Remove a status-timeline node.

        The mandatory initial ``seen`` node is immutable and cannot be deleted.
        Deleting the *last* node rolls the application status back to the last
        remaining node's status; if no nodes remain the status is reset to the
        initial ``seen`` state.
        """
        current = self._repo.get_by_id(event_id)
        if not current:
            raise NotFoundError(f"Status event {event_id} not found")
        if current.get("status") == ApplicationStatus.SEEN:
            raise ValidationError("The initial 'seen' status cannot be deleted")

        application_id = current.get("application_id") or ""
        timeline = self._repo.list_for_application(application_id)
        is_last = bool(timeline) and timeline[-1]["id"] == event_id

        self._repo.delete(event_id)

        if is_last and self._application_repo:
            remaining = self._repo.list_for_application(application_id)
            new_status = remaining[-1]["status"] if remaining else ApplicationStatus.SEEN
            self._application_repo.update(
                application_id,
                {"status": new_status, "updated_at": datetime.now(UTC).isoformat()},
            )

        self._emit(
            ApplicationStatusRemoved(
                aggregate_id=application_id,
                application_id=application_id,
                status=current.get("status") or "",
            )
        )

    def _emit(self, event: Any) -> None:
        try:
            self.event_publisher.publish(event)
        except Exception:  # noqa: BLE001 — best-effort publishing
            pass


__all__ = ["StatusEventService"]