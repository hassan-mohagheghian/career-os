"""Tests for skill domain events and the in-memory collector."""

from skills.domain.events import (
    SkillCategoryCreated,
    SkillCategoryDeleted,
    SkillCategoriesChanged,
    SkillBrokenDown,
    SkillCanonicalChanged,
)
from skills.domain.event_publisher import InMemoryEventCollector
from skills.application.use_cases.skill_category_service import SkillCategoryService
from skills.application.use_cases.skill_normalization_service import SkillNormalizationService


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

        b = SkillBrokenDown(skill_id=1, skill_name="Data Engineering", children=("Spark", "Airflow"))
        assert b.event_type == "skill.breakdown.created"
        assert b.children == ("Spark", "Airflow")

        p = SkillCanonicalChanged(skill_id=1, previous_name="React", new_name="ReactJS")
        assert p.event_type == "skill.canonical.changed"

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

        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        collector = InMemoryEventCollector()
        return SkillCategoryService(repo, collector), collector

    def _skill(self, sa_session):
        from skills.infrastructure.models.skill_model import SkillModel

        m = SkillModel(name="Python", source="user", source_type="user_input", user_id="test-user")
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


class TestSkillNormalizationService:
    def _service(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository

        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        collector = InMemoryEventCollector()
        return SkillNormalizationService(repo, collector), collector

    def _skill(self, sa_session, name="Python"):
        from skills.infrastructure.models.skill_model import SkillModel

        m = SkillModel(name=name, source="user", source_type="user_input", user_id="test-user")
        sa_session.add(m)
        sa_session.commit()
        sa_session.refresh(m)
        return m

    def test_break_down_emits_event(self, sa_session):
        from skills.infrastructure.models.skill_model import SkillAliasModel

        origin = self._skill(sa_session, "Data Engineering")
        child = self._skill(sa_session, "Spark")
        sa_session.add(SkillAliasModel(skill_id=child.id, alias_name="Spark", normalized_name="spark"))
        sa_session.commit()

        service, collector = self._service(sa_session)
        service.break_down(origin.id, ["Spark", "Airflow"])
        types = [e.event_type for e in collector.take_events()]
        assert "skill.breakdown.created" in types

    def test_promote_alias_emits_event(self, sa_session):
        from skills.infrastructure.models.skill_model import SkillAliasModel

        skill = self._skill(sa_session, "React")
        sa_session.add(SkillAliasModel(skill_id=skill.id, alias_name="ReactJS", normalized_name="reactjs"))
        sa_session.commit()

        service, collector = self._service(sa_session)
        result = service.promote_alias_to_canonical(skill.id, "ReactJS")
        assert result is not None
        types = [e.event_type for e in collector.take_events()]
        assert "skill.canonical.changed" in types
