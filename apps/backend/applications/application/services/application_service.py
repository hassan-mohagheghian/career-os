"""ApplicationService — creates and updates Application aggregate roots.

Domain events are emitted through the ApplicationEventPublisher port
(in-memory collector by default — EDD is incremental, no pub/sub yet).
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from applications.domain.entities.application import Application, ApplicationStatus
from applications.domain.event_publisher import ApplicationEventPublisher, InMemoryEventCollector
from applications.domain.events import ApplicationCreated, ApplicationUpdated
from shared.application.exceptions import NotFoundError, ValidationError

_UPDATABLE = ("status", "applied_at")


class ApplicationService:
    """Business operations for the Application aggregate."""

    def __init__(
        self,
        application_repo: Any,
        event_publisher: ApplicationEventPublisher | None = None,
    ):
        self._repo = application_repo
        self.event_publisher = event_publisher or InMemoryEventCollector()

    def get_by_job(self, job_id: str) -> dict[str, Any] | None:
        return self._repo.get_by_job_id(job_id)

    def create(self, job_id: str, status: str = ApplicationStatus.RECOMMENDED) -> dict[str, Any]:
        """Create an application for a job. Idempotent: reuses an existing one."""
        existing = self._repo.get_by_job_id(job_id)
        if existing:
            return existing
        self._validate_status(status)
        now = datetime.now(UTC).isoformat()
        stored = self._repo.create(
            {
                "job_id": job_id,
                "status": status,
                "applied_at": None,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._emit(
            ApplicationCreated(
                aggregate_id=stored["id"],
                application_id=stored["id"],
                job_id=job_id,
            )
        )
        return stored

    def update(self, application_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update status and/or applied date. Applied date may be cleared with None."""
        current = self._repo.get_by_id(application_id)
        if not current:
            raise NotFoundError(f"Application {application_id} not found")

        update: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
        if "status" in data and data["status"] is not None:
            self._validate_status(data["status"])
            update["status"] = data["status"]
        if "applied_at" in data:
            update["applied_at"] = data["applied_at"] or None

        if not any(k in update for k in _UPDATABLE):
            return current

        stored = self._repo.update(application_id, update) or current
        self._emit(
            ApplicationUpdated(
                aggregate_id=application_id,
                application_id=application_id,
                job_id=current.get("job_id") or "",
                status=stored.get("status") or "",
            )
        )
        return stored

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in ApplicationStatus.ALL:
            raise ValidationError(
                f"Invalid application status '{status}'; allowed: {', '.join(ApplicationStatus.ALL)}"
            )

    def _emit(self, event: Any) -> None:
        try:
            self.event_publisher.publish(event)
        except Exception:  # noqa: BLE001 — best-effort publishing
            pass


__all__ = ["ApplicationService"]
