"""Tests for skill domain events and the in-memory collector."""

from skills.domain.events import (
    SkillCategoryCreated,
    SkillCategoryDeleted,
    SkillCategoriesChanged,
)
from skills.domain.event_publisher import InMemoryEventCollector
from skills.application.use_cases.skill_category_service import SkillCategoryService


class TestSkillEvents:
    def test_event_dataclasses(self):
        e = SkillCategoryCreated(name="security", aggregate_id=7)
        assert e.event_type == "skill.category.created"
        assert e.name == "security"
        assert e.aggregate_id == 7

        d = SkillCategoryDeleted(name="security")
        assert d.event_type == "skill.category.deleted"

        c = SkillCategoriesChanged(skill_id=1, skill_name="K8s", categories=("technical",))
        assert c.event_type == "skill.categories.changed"

    def test_collector_records_events(self):
        collector = InMemoryEventCollector()
        collector.publish(SkillCategoryCreated(name="security"))
        assert len(collector.events) == 1
        drained = collector.take_events()
        assert len(drained) == 1
        assert collector.events == []


class TestSkillCategoryService:
    def _service(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository

        repo = SQLAlchemySkillRepository(sa_session)
        collector = InMemoryEventCollector()
        return SkillCategoryService(repo, collector), collector

    def _skill(self, sa_session):
        from skills.infrastructure.models.skill_model import SkillModel

        m = SkillModel(name="Python", source="user", source_type="user_input")
        sa_session.add(m)
        sa_session.commit()
        sa_session.refresh(m)
        return m

    def test_create_category_emits_event(self, sa_session):
        service, collector = self._service(sa_session)
        service.create_category("security")
        types = [e.event_type for e in collector.take_events()]
        assert "skill.category.created" in types

    def test_create_existing_category_no_event(self, sa_session):
        service, collector = self._service(sa_session)
        service.create_category("security")
        collector.take_events()
        service.create_category("security")
        assert collector.take_events() == []

    def test_delete_category_emits_event(self, sa_session):
        service, collector = self._service(sa_session)
        service.create_category("security")
        collector.take_events()
        service.delete_category("security")
        types = [e.event_type for e in collector.take_events()]
        assert "skill.category.deleted" in types

    def test_set_categories_emits_change_event(self, sa_session):
        m = self._skill(sa_session)
        service, collector = self._service(sa_session)
        service.set_skill_categories(m.id, ["technical"])
        events = collector.take_events()
        assert any(e.event_type == "skill.categories.changed" for e in events)

    def test_set_categories_no_event_when_unchanged(self, sa_session):
        m = self._skill(sa_session)
        service, collector = self._service(sa_session)
        service.set_skill_categories(m.id, ["technical"])
        collector.take_events()
        service.set_skill_categories(m.id, ["technical"])
        assert collector.take_events() == []
