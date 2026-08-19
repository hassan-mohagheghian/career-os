"""Domain events for the Placeholders bounded context.

Emitted when placeholder values change. EDD is incremental (AGENTS.md rule 16):
events are always defined, emitted and documented, but the default transport is
an in-memory collector.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class PlaceholdersUpdated(DomainEvent):
    """Placeholder values were created or updated in bulk."""

    keys: tuple[str, ...] = field(default_factory=tuple)
    event_type: str = "placeholders.updated"


__all__ = ["PlaceholdersUpdated"]