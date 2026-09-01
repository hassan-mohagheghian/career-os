"""Tests for skill multi-category management (catalog, M2M, alias inheritance)."""

from skills.infrastructure import SQLAlchemySkillRepository
from skills.infrastructure.models.skill_model import (
    SkillModel,
    SkillAliasModel,
    SkillCategoryModel,
)


def _skill(sa_session, **kwargs):
    defaults = dict(
        name="Python", level=1, category="", hidden=0, source="user",
        source_type="user_input", user_id="test-user",
    )
    defaults.update(kwargs)
    m = SkillModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    sa_session.refresh(m)
    return m


def _alias(sa_session, skill_id, alias_name):
    a = SkillAliasModel(
        skill_id=skill_id, alias_name=alias_name, normalized_name=alias_name.lower()
    )
    sa_session.add(a)
    sa_session.commit()
    return a


def _category(sa_session, name):
    c = SkillCategoryModel(name=name)
    sa_session.add(c)
    sa_session.commit()
    sa_session.refresh(c)
    return c


class TestCategoryCatalog:
    def test_create_category(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        result = repo.create_category("data")
        assert result["name"] == "data"
        assert result["created"] is True

        again = repo.create_category("data")
        assert again["id"] == result["id"]
        assert again["created"] is False

    def test_create_category_blank_returns_none(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        assert repo.create_category("   ") is None

    def test_delete_category_unused(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        repo.create_category("data")
        result = repo.delete_category("data")
        assert result["status"] == "deleted"

    def test_delete_category_not_found(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        result = repo.delete_category("nope")
        assert result["status"] == "not_found"

    def test_delete_category_in_use(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        skill = _skill(sa_session)
        repo.set_categories(skill.id, ["data"])
        result = repo.delete_category("data")
        assert result["status"] == "in_use"
        assert result["count"] == 1


class TestMultiCategory:
    def test_set_categories_replaces_and_syncs_primary(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        skill = _skill(sa_session)
        updated = repo.set_categories(skill.id, ["technical", "engineering"])
        assert updated["categories"] == ["technical", "engineering"]
        assert updated["category"] == "technical"

        row = sa_session.query(SkillModel).filter(SkillModel.id == skill.id).first()
        assert row.category == "technical"

    def test_set_categories_auto_creates_catalog_rows(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        skill = _skill(sa_session)
        repo.set_categories(skill.id, ["brand-new-cat"])
        names = [c["category"] for c in repo.get_categories()]
        assert "brand-new-cat" in names

    def test_set_categories_empty_clears(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        skill = _skill(sa_session)
        repo.set_categories(skill.id, ["technical"])
        cleared = repo.set_categories(skill.id, [])
        assert cleared["categories"] == []
        assert cleared["category"] == ""

    def test_set_categories_missing_skill(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        assert repo.set_categories(9999, ["technical"]) is None

    def test_get_by_id_includes_categories(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        skill = _skill(sa_session)
        repo.set_categories(skill.id, ["technical", "domain"])
        got = repo.get_by_id(skill.id)
        assert got["categories"] == ["technical", "domain"]

    def test_primary_category_backfill_in_effective_categories(self, sa_session):
        _category(sa_session, "technical")
        skill = _skill(sa_session, category="technical")
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        got = repo.get_by_id(skill.id)
        assert "technical" in got["categories"]


class TestGetCategories:
    def test_counts_visible_skills_only(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        a = _skill(sa_session, name="A", hidden=0)
        b = _skill(sa_session, name="B", hidden=1)
        repo.set_categories(a.id, ["technical"])
        repo.set_categories(b.id, ["technical"])
        counts = {c["category"]: c["count"] for c in repo.get_categories()}
        assert counts.get("technical", 0) == 1

    def test_includes_unused_catalog_categories_with_zero_count(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        repo.create_category("security")
        security = next(c for c in repo.get_categories() if c["category"] == "security")
        assert security["count"] == 0


class TestAliasInheritance:
    def test_alias_row_inherits_canonical_categories(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        kubernetes = _skill(sa_session, name="Kubernetes")
        k8s = _skill(sa_session, name="K8s")
        _alias(sa_session, kubernetes.id, "K8s")
        repo.set_categories(kubernetes.id, ["engineering", "technical"])
        got = repo.get_by_id(k8s.id)
        assert got["categories"] == ["engineering", "technical"]

    def test_alias_primary_falls_back_to_canonical(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        kubernetes = _skill(sa_session, name="Kubernetes")
        k8s = _skill(sa_session, name="K8s")
        _alias(sa_session, kubernetes.id, "K8s")
        repo.set_categories(kubernetes.id, ["engineering"])
        got = repo.get_by_id(k8s.id)
        assert got["category"] == "engineering"

    def test_own_categories_merge_with_inherited(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session, user_id="test-user")
        kubernetes = _skill(sa_session, name="Kubernetes")
        k8s = _skill(sa_session, name="K8s")
        _alias(sa_session, kubernetes.id, "K8s")
        repo.set_categories(kubernetes.id, ["engineering"])
        repo.set_categories(k8s.id, ["technical"])
        got = repo.get_by_id(k8s.id)
        assert set(got["categories"]) == {"engineering", "technical"}
