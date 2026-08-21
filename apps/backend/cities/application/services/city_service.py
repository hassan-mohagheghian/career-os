"""Application service for the Cities bounded context.

``CityService.ensure`` is the single entry point other contexts use to link a
raw location to a canonical city row: it normalizes the raw value to a unique
``(city, country)`` pair and finds-or-creates the row, returning its id.

EDD (AGENTS.md rule 16): the service emits domain events through its publisher
port; the default transport is an in-memory collector.
"""

from __future__ import annotations

from typing import Any

from cities.domain.entities.city import CityNormalizer
from cities.domain.events import CityCreated, CityMerged, CityCanonicalChanged
from cities.domain.repositories.city_repository import ICityRepository


class CityService:
    def __init__(self, repository: ICityRepository, event_publisher: Any | None = None):
        self._repository = repository
        self._events = event_publisher

    def normalize(self, raw: str | None) -> tuple[str, str]:
        """Normalize a raw location string to a canonical ``(city, country)``."""
        return CityNormalizer.normalize(raw)

    def ensure(
        self,
        city: str,
        country: str,
        original_text: str = "",
        address: str = "",
    ) -> dict[str, Any] | None:
        """Find or create the canonical city row and return it.

        Returns ``None`` when both city and country are empty (nothing to link).
        """
        city = (city or "").strip()
        country = (country or "").strip()
        if not city and not country:
            return None

        existing = self._repository.find_by_city_country(city, country)
        if existing is not None:
            return existing

        created = self._repository.create(
            {
                "city": city,
                "country": country,
                "original_text": original_text or None,
                "address": address or None,
            }
        )
        if self._events is not None:
            self._events.publish(
                CityCreated(city_id=created["id"], city=city, country=country)
            )
        return created

    def normalize_and_ensure(
        self,
        raw: str | None,
        address: str = "",
    ) -> dict[str, Any] | None:
        """Normalize a raw location string and ensure its canonical city row."""
        city, country = self.normalize(raw)
        return self.ensure(city, country, original_text=raw or "", address=address)

    # ── Merge / aliases ──────────────────────────────────────────

    def merge(self, target_id: str, source_ids: list[str]) -> dict[str, Any]:
        """Merge source cities into a target; returns the repo merge result."""
        result = self._repository.merge(target_id, source_ids)
        if self._events is not None and "target" in result:
            self._events.publish(
                CityMerged(
                    target_id=target_id,
                    target_name=result["target"].get("city") or "",
                    source_ids=tuple(result.get("merged") or []),
                )
            )
        return result

    def add_alias(self, city_id: str, alias_name: str) -> dict[str, Any] | None:
        return self._repository.add_alias(city_id, alias_name)

    def remove_alias(self, city_id: str, alias_name: str) -> dict[str, Any] | None:
        return self._repository.remove_alias(city_id, alias_name)

    def promote_alias_to_canonical(
        self, city_id: str, alias_name: str
    ) -> dict[str, Any] | None:
        """Make an alias the canonical name; the old canonical becomes an alias."""
        result = self._repository.promote_alias_to_canonical(city_id, alias_name)
        if result is None or "error" in result:
            return result
        if self._events is not None:
            self._events.publish(
                CityCanonicalChanged(
                    city_id=city_id,
                    previous_name=result.get("previous_name", ""),
                    new_name=alias_name,
                )
            )
        return result


__all__ = ["CityService"]