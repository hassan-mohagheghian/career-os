"""Domain events for the Applications bounded context.

Emitted as the application evolves: created, status/applied-date updated,
follow-ups added/completed/deleted, and generated documents persisted. All
events are immutable facts (AGENTS.md rule 16); the default transport is the
in-memory collector.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class ApplicationCreated(DomainEvent):
    """A new application was created for a job."""

    application_id: str = ""
    job_id: str = ""
    event_type: str = "application.created"


@dataclass(frozen=True)
class ApplicationUpdated(DomainEvent):
    """The application core changed (status or applied date)."""

    application_id: str = ""
    job_id: str = ""
    status: str = ""
    event_type: str = "application.updated"


@dataclass(frozen=True)
class ApplicationStatusChanged(DomainEvent):
    """The application entered a new status at a specific time."""

    application_id: str = ""
    status: str = ""
    changed_at: str | None = None
    event_type: str = "application.status.changed"


@dataclass(frozen=True)
class ApplicationStatusRemoved(DomainEvent):
    """A status-timeline node was removed by the user."""

    application_id: str = ""
    status: str = ""
    event_type: str = "application.status.removed"


@dataclass(frozen=True)
class ApplicationFollowUpAdded(DomainEvent):
    """A follow-up was added to an application."""

    application_id: str = ""
    follow_up_id: str = ""
    scheduled_at: str | None = None
    event_type: str = "application.follow_up.added"


@dataclass(frozen=True)
class ApplicationFollowUpUpdated(DomainEvent):
    """A follow-up was edited (date, note, completion)."""

    application_id: str = ""
    follow_up_id: str = ""
    completed: bool = False
    event_type: str = "application.follow_up.updated"


@dataclass(frozen=True)
class ApplicationFollowUpDeleted(DomainEvent):
    """A follow-up was removed."""

    application_id: str = ""
    follow_up_id: str = ""
    event_type: str = "application.follow_up.deleted"


@dataclass(frozen=True)
class ApplicationDocumentGenerated(DomainEvent):
    """An application document version was persisted."""

    application_id: str = ""
    document_id: str = ""
    document_type: str = ""
    version: int = 1
    event_type: str = "application.document.generated"


@dataclass(frozen=True)
class ApplicationDocumentUpdated(DomainEvent):
    """An application document was edited by the user."""

    application_id: str = ""
    document_id: str = ""
    document_type: str = ""
    version: int = 1
    event_type: str = "application.document.updated"


@dataclass(frozen=True)
class ApplicationDocumentDeleted(DomainEvent):
    """An application document version was removed."""

    application_id: str = ""
    document_id: str = ""
    document_type: str = ""
    event_type: str = "application.document.deleted"


__all__ = [
    "ApplicationCreated",
    "ApplicationUpdated",
    "ApplicationStatusChanged",
    "ApplicationStatusRemoved",
    "ApplicationFollowUpAdded",
    "ApplicationFollowUpUpdated",
    "ApplicationFollowUpDeleted",
    "ApplicationDocumentGenerated",
    "ApplicationDocumentUpdated",
    "ApplicationDocumentDeleted",
]
