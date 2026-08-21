"""Domain events for the Cities bounded context.

EDD is incremental (AGENTS.md rule 16): events are always defined, emitted and
documented. The default transport is an in-memory collector — no pub/sub yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class CityCreated(DomainEvent):
    """A new canonical city row was created during normalization."""

    city_id: str = ""
    city: str = ""
    country: str = ""
    event_type: str = "city.created"


@dataclass(frozen=True)
class CityLinked(DomainEvent):
    """An entity (job, company, profile) was linked to a city row."""

    city_id: str = ""
    target_type: str = ""  # "job" | "company" | "profile"
    target_id: str = ""
    event_type: str = "city.linked"


@dataclass(frozen=True)
class CityMerged(DomainEvent):
    """One or more source cities were merged into a target city."""

    target_id: str = ""
    target_name: str = ""
    source_ids: tuple[str, ...] = ()
    event_type: str = "city.merged"


@dataclass(frozen=True)
class CityCanonicalChanged(DomainEvent):
    """An alias was promoted to be the canonical city name."""

    city_id: str = ""
    previous_name: str = ""
    new_name: str = ""
    event_type: str = "city.canonical.changed"


__all__ = ["CityCreated", "CityLinked", "CityMerged", "CityCanonicalChanged"]