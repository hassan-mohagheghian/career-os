"""Tests for skill management: hide and merge."""

import pytest
from sqlalchemy.exc import IntegrityError

from skills.infrastructure.models.skill_model import (
    SkillModel,
    SkillRelationshipModel,
)


def _merge(session, target_id, source_ids):
    """Core merge logic extracted from the endpoint."""
    target = session.query(SkillModel).filter(SkillModel.id == target_id).first()
    if not target:
        return None
    target_name = target.name
    merged = []
    for sid in source_ids:
        source = session.query(SkillModel).filter(SkillModel.id == sid).first()
        if not source or source.name == target_name:
            continue
        source_name = source.name
        session.delete(source)
        merged.append(source_name)
    session.commit()
    return merged


class TestMergeSkills:
    def test_merge_removes_source(self, sa_session):
        s1 = SkillModel(name="PostgreSQL", level=3, source="user", user_id="test-user")
        s2 = SkillModel(name="postgres", level=2, source="service", user_id="test-user")
        sa_session.add_all([s1, s2])
        sa_session.commit()

        merged = _merge(sa_session, s1.id, [s2.id])
        assert merged == ["postgres"]

        tech = sa_session.query(SkillModel.name).all()
        assert len(tech) == 1
        assert tech[0][0] == "PostgreSQL"

    def test_hide_skill(self, sa_session):
        m = SkillModel(name="CSS", level=1, source="service", user_id="test-user")
        sa_session.add(m)
        sa_session.commit()

        m.hidden = 1
        sa_session.commit()

        row = sa_session.query(SkillModel).filter(SkillModel.id == m.id).first()
        assert row.hidden == 1

        visible = sa_session.query(SkillModel.name).filter(SkillModel.hidden == 0).all()
        assert len(visible) == 0

    def test_merge_skips_self(self, sa_session):
        m = SkillModel(name="Python", level=4, source="user", user_id="test-user")
        sa_session.add(m)
        sa_session.commit()

        merged = _merge(sa_session, m.id, [m.id])
        assert merged == []
        assert sa_session.query(SkillModel).count() == 1

    def test_merge_multiple_sources(self, sa_session):
        s1 = SkillModel(name="React", level=4, source="user", user_id="test-user")
        s2 = SkillModel(name="ReactJS", level=3, source="service", user_id="test-user")
        s3 = SkillModel(name="react.js", level=2, source="service", user_id="test-user")
        sa_session.add_all([s1, s2, s3])
        sa_session.commit()

        merged = _merge(sa_session, s1.id, [s2.id, s3.id])
        assert set(merged) == {"ReactJS", "react.js"}

        tech = sa_session.query(SkillModel.name).order_by(SkillModel.id).all()
        assert len(tech) == 1
        assert tech[0][0] == "React"

    def test_merge_user_into_service(self, sa_session):
        s1 = SkillModel(name="PostgreSQL", level=3, source="user", user_id="test-user")
        s2 = SkillModel(name="postgres", level=2, source="service", user_id="test-user")
        sa_session.add_all([s1, s2])
        sa_session.commit()

        merged = _merge(sa_session, s1.id, [s2.id])
        assert merged == ["postgres"]
        assert sa_session.query(SkillModel).filter(SkillModel.id == s1.id).first().source == "user"


class TestSkillTaxonomy:
    def test_category_filter(self, sa_session):
        sa_session.add(SkillModel(name="Python", level=4, category="technical", user_id="test-user"))
        sa_session.add(SkillModel(name="Leadership", level=3, category="professional", user_id="test-user"))
        sa_session.commit()

        tech = sa_session.query(SkillModel.name).filter(SkillModel.category == "technical").all()
        assert len(tech) == 1
        assert tech[0][0] == "Python"

        prof = sa_session.query(SkillModel.name).filter(SkillModel.category == "professional").all()
        assert len(prof) == 1
        assert prof[0][0] == "Leadership"

    def test_hidden_skills_list(self, sa_session):
        sa_session.add(SkillModel(name="CSS", level=1, hidden=0, user_id="test-user"))
        sa_session.add(SkillModel(name="jQuery", level=1, hidden=1, user_id="test-user"))
        sa_session.commit()

        hidden = sa_session.query(SkillModel.name).filter(SkillModel.hidden == 1).all()
        assert len(hidden) == 1
        assert hidden[0][0] == "jQuery"

    def test_restore_hidden_skill(self, sa_session):
        m = SkillModel(name="jQuery", level=1, hidden=1, user_id="test-user")
        sa_session.add(m)
        sa_session.commit()

        m.hidden = 0
        sa_session.commit()

        row = sa_session.query(SkillModel).filter(SkillModel.id == m.id).first()
        assert row.hidden == 0


class TestSkillRelationships:
    def test_create_relationship(self, sa_session):
        sa_session.add(
            SkillRelationshipModel(
                skill_name="React", related_name="ReactJS", relation_type="similar", confidence=0.9
            )
        )
        sa_session.commit()

        row = sa_session.query(SkillRelationshipModel).filter(
            SkillRelationshipModel.skill_name == "React"
        ).first()
        assert row is not None
        assert row.relation_type == "similar"

    def test_query_relationships_bidirectional(self, sa_session):
        sa_session.add(
            SkillRelationshipModel(
                skill_name="React", related_name="ReactJS", relation_type="similar", confidence=0.9
            )
        )
        sa_session.commit()

        rows = sa_session.query(SkillRelationshipModel).filter(
            (SkillRelationshipModel.skill_name == "React")
            | (SkillRelationshipModel.related_name == "React")
        ).all()
        assert len(rows) == 1

    def test_delete_relationship(self, sa_session):
        rel = SkillRelationshipModel(
            skill_name="React", related_name="ReactJS", relation_type="similar", confidence=0.9
        )
        sa_session.add(rel)
        sa_session.commit()

        sa_session.delete(rel)
        sa_session.commit()

        rows = sa_session.query(SkillRelationshipModel).all()
        assert len(rows) == 0

    def test_unique_constraint(self, sa_session):
        sa_session.add(
            SkillRelationshipModel(
                skill_name="React", related_name="ReactJS", relation_type="similar", confidence=0.9
            )
        )
        sa_session.commit()

        with pytest.raises(IntegrityError):
            sa_session.add(
                SkillRelationshipModel(
                    skill_name="React", related_name="ReactJS", relation_type="similar", confidence=0.8
                )
            )
            sa_session.commit()
