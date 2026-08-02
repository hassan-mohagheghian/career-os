"""Company domain events."""

from dataclasses import dataclass
from typing import Optional

from shared.domain.domain_event import DomainEvent
from shared.domain.lifecycle import LifecycleStatus


@dataclass(frozen=True)
class CompanyQueued(DomainEvent):
    aggregate_id: int
    event_type: str = "company.queued"


@dataclass(frozen=True)
class CompanyProcessingStarted(DomainEvent):
    aggregate_id: int
    event_type: str = "company.processing_started"


@dataclass(frozen=True)
class CompanyProgressUpdated(DomainEvent):
    aggregate_id: int
    current_node: str = ""
    progress_pct: float = 0.0
    message: str = ""
    event_type: str = "company.progress_updated"


@dataclass(frozen=True)
class CompanyCompleted(DomainEvent):
    aggregate_id: int
    event_type: str = "company.completed"


@dataclass(frozen=True)
class CompanyFailed(DomainEvent):
    aggregate_id: int
    reason: str = ""
    workflow_step: str = ""
    retry_count: int = 0
    event_type: str = "company.failed"


@dataclass(frozen=True)
class CompanyCancelled(DomainEvent):
    aggregate_id: int
    event_type: str = "company.cancelled"
