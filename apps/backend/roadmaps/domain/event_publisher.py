"""RoadmapEventPublisher — the domain event port for the Roadmaps context.

EDD is incremental in this repo (see AGENTS.md rule 16): domain events are
always defined, emitted and documented, but the default implementation is an
in-memory collector — no Redis, no SSE, no outbox. A real transport is wired to
this port in a dedicated later phase without touching the domain or application
layers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from shared.domain.domain_event import DomainEvent


class RoadmapEventPublisher(ABC):
    """Port through which the Roadmaps context publishes domain events."""

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event (best-effort)."""
        ...

    def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.publish(event)


class InMemoryEventCollector(RoadmapEventPublisher):
    """Default in-memory implementation that records events for observability.

    Tests and callers can read collected events via ``events`` or drain them
    with ``take_events()``. No transport is involved.
    """

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

    def take_events(self) -> list[DomainEvent]:
        events, self._events = list(self._events), []
        return events

    def as_dicts(self) -> list[dict[str, Any]]:
        return [
            {
                "event_type": e.event_type,
                "aggregate_id": getattr(e, "aggregate_id", None),
                "roadmap_id": getattr(e, "roadmap_id", None),
                "status": getattr(e, "status", None),
            }
            for e in self._events
        ]


__all__ = ["RoadmapEventPublisher", "InMemoryEventCollector"]