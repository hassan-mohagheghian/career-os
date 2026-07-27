"""Tests for skill management: hide and merge."""

import pytest
from sqlalchemy.exc import IntegrityError

from infrastructure.database.models.skill_model import (
    SkillModel,
    SkillRelationshipModel,
)
from infrastructure.database.models.misc_models import (
    SkillRoadmapModel,
    SkillRoadmapJobModel,
    SkillRoadmapProgressModel,
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
        session.query(SkillRoadmapModel).filter(
            SkillRoadmapModel.skill_name == source_name
        ).update({"skill_name": target_name})
        session.query(SkillRoadmapProgressModel).filter(
            SkillRoadmapProgressModel.skill_name == source_name
        ).update({"skill_name": target_name})
        session.query(SkillRoadmapJobModel).filter(
            SkillRoadmapJobModel.skill_name == source_name
        ).update({"skill_name": target_name})
        session.delete(source)
        merged.append(source_name)
    session.commit()
    return merged


class TestMergeSkills:
    def test_merge_renames_roadmaps(self, sa_session):
        sa_session.add(SkillModel(name="PostgreSQL", level=3, source="user"))
        sa_session.add(SkillModel(name="postgres", level=2, source="service"))
        sa_session.flush()
        sa_session.add(
            SkillRoadmapModel(skill_name="postgres", title="Basics", level=1)
        )
        sa_session.flush()
        sa_session.add(
            SkillRoadmapProgressModel(roadmap_id=1, skill_name="postgres", completed=1)
        )
        sa_session.add(
            SkillRoadmapJobModel(skill_name="postgres", status="completed")
        )
        sa_session.commit()

        merged = _merge(sa_session, 1, [2])
        assert merged == ["postgres"]

        roads = sa_session.query(SkillRoadmapModel.skill_name).all()
        progress = sa_session.query(SkillRoadmapProgressModel.skill_name).all()
        jobs = sa_session.query(SkillRoadmapJobModel.skill_name).all()
        tech = sa_session.query(SkillModel.name).all()

        assert all(r[0] == "PostgreSQL" for r in roads)
        assert all(r[0] == "PostgreSQL" for r in progress)
        assert all(r[0] == "PostgreSQL" for r in jobs)
        assert len(tech) == 1
        assert tech[0][0] == "PostgreSQL"

    def test_hide_skill(self, sa_session):
        m = SkillModel(name="CSS", level=1, source="service")
        sa_session.add(m)
        sa_session.commit()

        m.hidden = 1
        sa_session.commit()

        row = sa_session.query(SkillModel).filter(SkillModel.id == m.id).first()
        assert row.hidden == 1

        visible = sa_session.query(SkillModel.name).filter(SkillModel.hidden == 0).all()
        assert len(visible) == 0

    def test_merge_skips_self(self, sa_session):
        sa_session.add(SkillModel(name="Python", level=4, source="user"))
        sa_session.commit()

        merged = _merge(sa_session, 1, [1])
        assert merged == []
        assert sa_session.query(SkillModel).count() == 1

    def test_merge_multiple_sources(self, sa_session):
        sa_session.add(SkillModel(name="React", level=4, source="user"))
        sa_session.add(SkillModel(name="ReactJS", level=3, source="service"))
        sa_session.add(SkillModel(name="react.js", level=2, source="service"))
        sa_session.flush()
        sa_session.add(
            SkillRoadmapModel(skill_name="ReactJS", title="Basics", level=1)
        )
        sa_session.flush()
        sa_session.add(
            SkillRoadmapProgressModel(roadmap_id=1, skill_name="ReactJS", completed=1)
        )
        sa_session.commit()

        merged = _merge(sa_session, 1, [2, 3])
        assert set(merged) == {"ReactJS", "react.js"}

        roads = sa_session.query(SkillRoadmapModel.skill_name).all()
        assert all(r[0] == "React" for r in roads)

        tech = sa_session.query(SkillModel.name).order_by(SkillModel.id).all()
        assert len(tech) == 1
        assert tech[0][0] == "React"

    def test_merge_user_into_service(self, sa_session):
        """User-input skill can merge with service-detected skill and vice versa."""
        sa_session.add(SkillModel(name="PostgreSQL", level=3, source="user"))
        sa_session.add(SkillModel(name="postgres", level=2, source="service"))
        sa_session.commit()

        merged = _merge(sa_session, 1, [2])
        assert merged == ["postgres"]
        assert sa_session.query(SkillModel).filter(SkillModel.id == 1).first().source == "user"


class TestSkillTaxonomy:
    def test_category_filter(self, sa_session):
        sa_session.add(SkillModel(name="Python", level=4, category="technical"))
        sa_session.add(SkillModel(name="Leadership", level=3, category="professional"))
        sa_session.commit()

        tech = sa_session.query(SkillModel.name).filter(SkillModel.category == "technical").all()
        assert len(tech) == 1
        assert tech[0][0] == "Python"

        prof = sa_session.query(SkillModel.name).filter(SkillModel.category == "professional").all()
        assert len(prof) == 1
        assert prof[0][0] == "Leadership"

    def test_hidden_skills_list(self, sa_session):
        sa_session.add(SkillModel(name="CSS", level=1, hidden=0))
        sa_session.add(SkillModel(name="jQuery", level=1, hidden=1))
        sa_session.commit()

        hidden = sa_session.query(SkillModel.name).filter(SkillModel.hidden == 1).all()
        assert len(hidden) == 1
        assert hidden[0][0] == "jQuery"

    def test_restore_hidden_skill(self, sa_session):
        m = SkillModel(name="jQuery", level=1, hidden=1)
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
