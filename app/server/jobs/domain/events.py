"""Job domain events."""

from dataclasses import dataclass
from typing import Optional

from shared.domain.domain_event import DomainEvent
from shared.domain.lifecycle import LifecycleStatus


@dataclass(frozen=True)
class JobQueued(DomainEvent):
    aggregate_id: int
    event_type: str = "job.queued"


@dataclass(frozen=True)
class JobProcessingStarted(DomainEvent):
    aggregate_id: int
    event_type: str = "job.processing_started"


@dataclass(frozen=True)
class JobProgressUpdated(DomainEvent):
    aggregate_id: int
    current_node: str = ""
    progress_pct: float = 0.0
    message: str = ""
    event_type: str = "job.progress_updated"


@dataclass(frozen=True)
class JobCompleted(DomainEvent):
    aggregate_id: int
    event_type: str = "job.completed"


@dataclass(frozen=True)
class JobFailed(DomainEvent):
    aggregate_id: int
    reason: str = ""
    workflow_step: str = ""
    retry_count: int = 0
    event_type: str = "job.failed"


@dataclass(frozen=True)
class JobCancelled(DomainEvent):
    aggregate_id: int
    event_type: str = "job.cancelled"
