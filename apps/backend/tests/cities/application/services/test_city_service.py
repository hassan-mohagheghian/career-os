"""Tests for CityService — ensure/normalize-and-ensure and event emission."""

from cities.application.services.city_service import CityService
from cities.domain.event_publisher import InMemoryEventCollector
from cities.infrastructure.models.city_model import CityModel
from cities.infrastructure.repositories.sa_city_repository import SQLAlchemyCityRepository


class TestCityService:
    def test_ensure_creates_and_is_idempotent(self, sa_session):
        service = CityService(SQLAlchemyCityRepository(sa_session), InMemoryEventCollector())
        first = service.ensure("Berlin", "Germany", original_text="Berlin, Germany")
        second = service.ensure("berlin", "germany", original_text="berlin")
        assert first["id"] == second["id"]
        assert first["city"] == "Berlin"
        assert first["country"] == "Germany"
        assert sa_session.query(CityModel).count() == 1

    def test_ensure_returns_none_when_empty(self, sa_session):
        service = CityService(SQLAlchemyCityRepository(sa_session))
        assert service.ensure("", "") is None

    def test_normalize_and_ensure_wires_canonical_row(self, sa_session):
        service = CityService(SQLAlchemyCityRepository(sa_session))
        row = service.normalize_and_ensure("München")
        assert row["city"] == "Munich"
        assert row["country"] == "Germany"
        assert row["original_text"] == "München"

    def test_emits_city_created_event(self, sa_session):
        collector = InMemoryEventCollector()
        service = CityService(SQLAlchemyCityRepository(sa_session), collector)
        service.ensure("Berlin", "Germany")
        assert len(collector.events) == 1
        assert collector.events[0].event_type == "city.created"
        assert collector.events[0].city == "Berlin"

    def test_no_duplicate_event_on_existing(self, sa_session):
        collector = InMemoryEventCollector()
        service = CityService(SQLAlchemyCityRepository(sa_session), collector)
        service.ensure("Berlin", "Germany")
        service.ensure("Berlin", "Germany")
        assert len(collector.events) == 1

    def test_merge_emits_city_merged_event(self, sa_session):
        collector = InMemoryEventCollector()
        service = CityService(SQLAlchemyCityRepository(sa_session), collector)
        target = service.ensure("Munich", "Germany")
        source = service.ensure("München", "Germany")

        service.merge(target["id"], [source["id"]])

        assert collector.events[-1].event_type == "city.merged"
        assert collector.events[-1].target_id == target["id"]
        assert collector.events[-1].source_ids == ("München",)

    def test_promote_emits_city_canonical_changed_event(self, sa_session):
        collector = InMemoryEventCollector()
        service = CityService(SQLAlchemyCityRepository(sa_session), collector)
        city = service.ensure("Munich", "Germany")
        service.add_alias(city["id"], "München")

        service.promote_alias_to_canonical(city["id"], "München")

        assert collector.events[-1].event_type == "city.canonical.changed"
        assert collector.events[-1].previous_name == "Munich"
        assert collector.events[-1].new_name == "München"