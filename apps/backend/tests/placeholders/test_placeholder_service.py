"""Tests for the Placeholders service and substitution logic."""

from __future__ import annotations

from placeholders.application.services.placeholder_service import PlaceholderService
from placeholders.domain.entities.placeholder import PlaceholderKey, fill_placeholders
from placeholders.domain.events import PlaceholdersUpdated


class RecordingCollector:
    def __init__(self):
        self._events = []

    def publish(self, event):
        self._events.append(event)

    @property
    def events(self):
        return list(self._events)


class FakeRepo:
    def __init__(self):
        self._rows: dict[str, dict] = {}

    def get_all(self):
        return [self._rows[k] for k in sorted(self._rows)]

    def get_by_key(self, key):
        return self._rows.get(key)

    def upsert(self, key, value):
        row = self._rows.get(key) or {"key": key}
        row.update({"key": key, "value": value})
        self._rows[key] = row
        return row


class TestFillPlaceholders:
    def test_substitutes_known_tokens(self):
        content = "Name: {{name}} | Email: {{email}}"
        assert fill_placeholders(content, {"name": "Hassan", "email": "h@x.com"}) == (
            "Name: Hassan | Email: h@x.com"
        )

    def test_unknown_token_left_intact(self):
        content = "{{unknown}} and {{email}}"
        assert fill_placeholders(content, {"email": "h@x.com"}) == "{{unknown}} and h@x.com"

    def test_case_insensitive_and_whitespace(self):
        assert fill_placeholders("{{  Name }}", {"name": "Hassan"}) == "Hassan"

    def test_no_tokens_unchanged(self):
        assert fill_placeholders("plain text", {}) == "plain text"


class TestPlaceholderKey:
    def test_known_keys_have_labels(self):
        assert PlaceholderKey.NAME in PlaceholderKey.ALL
        assert PlaceholderKey.LABELS[PlaceholderKey.EMAIL] == "Email"


class TestPlaceholderService:
    def _service(self):
        collector = RecordingCollector()
        return PlaceholderService(FakeRepo(), collector), collector

    def test_list_and_get_map(self):
        service, _ = self._service()
        service.upsert_many({"name": "Hassan", "email": "h@x.com"})
        assert service.get_map() == {"name": "Hassan", "email": "h@x.com"}
        assert {i["key"] for i in service.list()} == {"name", "email"}

    def test_upsert_emits_event(self):
        service, collector = self._service()
        service.upsert_many({"name": "Hassan"})
        assert any(
            isinstance(e, PlaceholdersUpdated) and "name" in e.keys for e in collector.events
        )

    def test_upsert_is_idempotent(self):
        service, _ = self._service()
        service.upsert_many({"name": "A"})
        service.upsert_many({"name": "B"})
        assert service.get_map()["name"] == "B"

    def test_fill_uses_stored_values(self):
        service, _ = self._service()
        service.upsert_many({"name": "Hassan", "email": "h@x.com"})
        assert service.fill("Hi {{name}}, contact {{email}}") == "Hi Hassan, contact h@x.com"

    def test_fill_unknown_token_left(self):
        service, _ = self._service()
        service.upsert_many({"name": "Hassan"})
        assert service.fill("{{name}} {{missing}}") == "Hassan {{missing}}"

    def test_keys_returns_canonical_catalog(self):
        service, _ = self._service()
        assert set(service.keys()) == set(PlaceholderKey.ALL)