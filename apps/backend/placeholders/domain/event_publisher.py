"""PlaceholderEventPublisher — the domain event port for the Placeholders context.

EDD is incremental in this repo (AGENTS.md rule 16): events are defined, emitted
and documented, but the default implementation is an in-memory collector — no
pub/sub transport yet. A real transport is wired to this port later without
touching the domain or application layers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from shared.domain.domain_event import DomainEvent


class PlaceholderEventPublisher(ABC):
    """Port through which the Placeholders context publishes domain events."""

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event (best-effort)."""
        ...

    def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.publish(event)


class InMemoryEventCollector(PlaceholderEventPublisher):
    """Default in-memory implementation that records events for observability."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

    def take_events(self) -> list[DomainEvent]:
        events = self._events
        self._events = []
        return events

    def __len__(self) -> int:
        return len(self._events)


__all__ = ["PlaceholderEventPublisher", "InMemoryEventCollector"]