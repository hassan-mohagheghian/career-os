"""PlaceholderService — business operations for named placeholder values.

Owns the CRUD of placeholder values and the token substitution used when a
generated document is served or exported to PDF. Domain events are emitted
best-effort through the event publisher port (EDD, in-memory collector).
"""

from __future__ import annotations

from typing import Any

from placeholders.domain.entities.placeholder import PlaceholderKey, fill_placeholders
from placeholders.domain.event_publisher import PlaceholderEventPublisher, InMemoryEventCollector
from placeholders.domain.events import PlaceholdersUpdated


class PlaceholderService:
    """Business operations for the Placeholders aggregate."""

    def __init__(
        self,
        repo: Any,
        event_publisher: PlaceholderEventPublisher | None = None,
    ):
        self._repo = repo
        self.event_publisher = event_publisher or InMemoryEventCollector()

    def list(self) -> list[dict[str, Any]]:
        """Return every saved placeholder, ordered by key."""
        return self._repo.get_all()

    def get_map(self) -> dict[str, str]:
        """Return ``{key: value}`` for all saved placeholders."""
        return {row["key"]: row["value"] or "" for row in self._repo.get_all()}

    def upsert_many(self, values: dict[str, str]) -> list[dict[str, Any]]:
        """Upsert a set of placeholder values and emit an update event."""
        stored: list[dict[str, Any]] = []
        changed_keys: list[str] = []
        for key, value in values.items():
            if not str(key).strip():
                continue
            row = self._repo.upsert(str(key).strip(), str(value or ""))
            stored.append(row)
            changed_keys.append(row["key"])
        if changed_keys:
            self._emit(PlaceholdersUpdated(keys=tuple(changed_keys)))
        return stored

    def fill(self, content: str) -> str:
        """Replace every ``{{key}}`` token in ``content`` with its stored value."""
        if not content:
            return content
        return fill_placeholders(content, self.get_map())

    @staticmethod
    def keys() -> list[str]:
        """Canonical placeholder keys the Placeholders page edits."""
        return list(PlaceholderKey.ALL)

    def _emit(self, event: Any) -> None:
        try:
            self.event_publisher.publish(event)
        except Exception:  # noqa: BLE001 — best-effort publishing
            pass


__all__ = ["PlaceholderService"]