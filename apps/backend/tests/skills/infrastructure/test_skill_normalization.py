"""Tests for skill normalization: slug resolution, break-down, promote-to-canonical."""

from skills.infrastructure.models.skill_model import (
    SkillModel,
    SkillAliasModel,
    SkillMentionModel,
    SkillBreakdownModel,
    SkillCategoryModel,
)
from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository
from skills.domain.slug_utils import slugify


class TestSlugify:
    def test_lowercases_and_normalizes(self):
        assert slugify("NoSQL") == "nosql"
        assert slugify("Data Engineering") == "data-engineering"
        assert slugify("C#") == "c#"
        assert slugify("React.js") == "react.js"
        assert slugify("  Python  ") == "python"

    def test_blank_returns_empty(self):
        assert slugify(None) == ""
        assert slugify("") == ""
        assert slugify("   ") == ""


class TestSlugOnModel:
    def test_slug_derived_from_name(self, sa_session):
        skill = SkillModel(name="NoSQL", source="user")
        sa_session.add(skill)
        sa_session.commit()
        assert skill.slug == "nosql"


class TestResolveSkillBySlug:
    def test_resolves_by_canonical_slug(self, sa_session):
        existing = SkillModel(name="NoSQL", source="user")
        sa_session.add(existing)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        skill_id = repo.resolve_skill({"name": "nosql", "category": "database"})
        assert skill_id == existing.id

    def test_resolves_case_insensitively(self, sa_session):
        existing = SkillModel(name="React", source="user")
        sa_session.add(existing)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        assert repo.resolve_skill({"name": "REACT"}) == existing.id

    def test_resolves_by_alias_slug(self, sa_session):
        skill = SkillModel(name="React", source="user")
        sa_session.add(skill)
        sa_session.flush()
        sa_session.add(SkillAliasModel(skill_id=skill.id, alias_name="ReactJS", normalized_name="reactjs"))
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        assert repo.resolve_skill({"name": "reactjs"}) == skill.id


class TestBreakDown:
    def test_break_down_splits_and_hides_origin(self, sa_session):
        origin = SkillModel(name="Data Engineering", source="user")
        sa_session.add(origin)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        result = repo.break_down(origin.id, ["Spark", "Airflow"])

        assert "error" not in result
        assert result["hidden"] is True
        assert len(result["children"]) == 2

        rows = sa_session.query(SkillBreakdownModel).all()
        assert len(rows) == 2

        origin = sa_session.query(SkillModel).filter(SkillModel.id == origin.id).first()
        assert origin.hidden == 1

    def test_break_down_duplicates_mentions_to_children(self, sa_session):
        origin = SkillModel(name="Data Engineering", source="user")
        sa_session.add(origin)
        sa_session.commit()
        repo = SQLAlchemySkillRepository(sa_session)
        repo.upsert_mentions(origin.id, "job", "job-1")

        result = repo.break_down(origin.id, ["Spark", "Airflow"])

        for child in result["children"]:
            assert repo.get_mention_counts([child["id"]])[child["id"]] == 1

    def test_break_down_requires_two_distinct_children(self, sa_session):
        origin = SkillModel(name="Data Engineering", source="user")
        sa_session.add(origin)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        result = repo.break_down(origin.id, ["Spark"])
        assert "error" in result

    def test_break_down_missing_origin(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session)
        result = repo.break_down(9999, ["Spark", "Airflow"])
        assert "error" in result

    def test_get_breakdown_map(self, sa_session):
        origin = SkillModel(name="Data Engineering", source="user")
        sa_session.add(origin)
        sa_session.commit()
        repo = SQLAlchemySkillRepository(sa_session)
        repo.break_down(origin.id, ["Spark", "Airflow"])

        mapping = repo.get_breakdown_map()
        assert len(mapping) == 1
        assert mapping[0]["origin"]["name"] == "Data Engineering"
        assert {c["name"] for c in mapping[0]["children"]} == {"Spark", "Airflow"}

    def test_list_breakdowns_for_origin_and_child(self, sa_session):
        origin = SkillModel(name="Data Engineering", source="user")
        sa_session.add(origin)
        sa_session.commit()
        repo = SQLAlchemySkillRepository(sa_session)
        result = repo.break_down(origin.id, ["Spark", "Airflow"])

        child_id = result["children"][0]["id"]
        info = repo.list_breakdowns(origin.id)
        assert len(info["children"]) == 2
        child_info = repo.list_breakdowns(child_id)
        assert child_info["origin"]["id"] == origin.id


class TestPromoteAliasToCanonical:
    def test_promotes_alias(self, sa_session):
        skill = SkillModel(name="React", source="user")
        sa_session.add(skill)
        sa_session.flush()
        sa_session.add(SkillAliasModel(skill_id=skill.id, alias_name="ReactJS", normalized_name="reactjs"))
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        result = repo.promote_alias_to_canonical(skill.id, "ReactJS")

        assert result is not None
        assert result["name"] == "ReactJS"
        assert "React" in result["aliases"]

    def test_promote_returns_none_when_alias_missing(self, sa_session):
        skill = SkillModel(name="React", source="user")
        sa_session.add(skill)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        assert repo.promote_alias_to_canonical(skill.id, "DoesNotExist") is None

    def test_promote_returns_none_on_slug_collision(self, sa_session):
        a = SkillModel(name="React", source="user")
        b = SkillModel(name="ReactJS", source="user")
        sa_session.add_all([a, b])
        sa_session.flush()
        sa_session.add(SkillAliasModel(skill_id=a.id, alias_name="reactjs", normalized_name="reactjs"))
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        assert repo.promote_alias_to_canonical(a.id, "reactjs") is None


class TestNormalizeAll:
    def test_merges_slug_collisions(self, sa_session):
        s1 = SkillModel(name="NoSQL", slug="nosql", source="user")
        s2 = SkillModel(name="nosql", slug="legacy-nosql", source="service")
        sa_session.add_all([s1, s2])
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        stats = repo.normalize_all()

        assert stats["skills_hidden"] == 1
        visible = sa_session.query(SkillModel).filter(SkillModel.hidden == 0).all()
        assert len(visible) == 1
        assert visible[0].name == "NoSQL"

    def test_merges_category_slug_collisions(self, sa_session):
        c1 = SkillCategoryModel(name="Data Engineering", slug="data-engineering")
        c2 = SkillCategoryModel(name="data engineering", slug="legacy-data-engineering")
        sa_session.add_all([c1, c2])
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        stats = repo.normalize_all()

        assert stats["categories_removed"] == 1
        remaining = sa_session.query(SkillCategoryModel).all()
        assert len(remaining) == 1
        assert remaining[0].name == "Data Engineering"
