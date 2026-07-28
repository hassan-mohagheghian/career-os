"""Base Domain Event and event infrastructure.

Domain events represent something that happened in the domain.
They are immutable and carry data about the occurrence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


def _default_event_type(instance: DomainEvent) -> str:
    """Derive event type from class name."""
    return instance.__class__.__name__


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Events represent things that happened in the domain.
    They are immutable and carry relevant data.

    Attributes:
        event_id: Unique identifier for this event occurrence
        occurred_at: When the event occurred
        aggregate_id: ID of the aggregate root this event relates to
        event_type: String identifier for the event type
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: Any = None
    event_type: str = ""
