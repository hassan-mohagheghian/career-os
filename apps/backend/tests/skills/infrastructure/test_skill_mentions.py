"""Tests for skill mentions (job/company demand links)."""

from skills.infrastructure.models.skill_model import SkillModel, SkillAliasModel, SkillMentionModel
from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository


class TestResolveSkill:
    def test_creates_new_skill(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session)
        skill_id = repo.resolve_skill({"name": "Kubernetes", "category": "engineering", "source_type": "ai_generated"})

        row = sa_session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        assert row is not None
        assert row.name == "Kubernetes"
        assert row.category == "engineering"
        assert row.source_type == "ai_generated"

    def test_matches_existing_by_name(self, sa_session):
        existing = SkillModel(name="Python", source="user", source_type="user_input")
        sa_session.add(existing)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        skill_id = repo.resolve_skill({"name": "Python"})
        assert skill_id == existing.id
        assert sa_session.query(SkillModel).count() == 1

    def test_matches_existing_by_alias(self, sa_session):
        skill = SkillModel(name="React", source="user")
        sa_session.add(skill)
        sa_session.flush()
        sa_session.add(SkillAliasModel(skill_id=skill.id, alias_name="ReactJS", normalized_name="reactjs"))
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        skill_id = repo.resolve_skill({"name": "ReactJS"})
        assert skill_id == skill.id
        assert sa_session.query(SkillModel).count() == 1


class TestSkillMentions:
    def test_upsert_and_count(self, sa_session):
        skill = SkillModel(name="Kafka", source="user")
        sa_session.add(skill)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        repo.upsert_mentions(skill.id, "job", "job-uuid-1", status="matched", evidence="[]")
        repo.upsert_mentions(skill.id, "company", "company-uuid-1")

        assert repo.get_mention_counts([skill.id]) == {skill.id: 2}

    def test_upsert_is_idempotent_per_source(self, sa_session):
        skill = SkillModel(name="Docker", source="user")
        sa_session.add(skill)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        repo.upsert_mentions(skill.id, "job", "job-uuid-1", status="matched")
        repo.upsert_mentions(skill.id, "job", "job-uuid-1", status="low")

        assert sa_session.query(SkillMentionModel).count() == 1
        row = sa_session.query(SkillMentionModel).one()
        assert row.status == "low"
        assert repo.get_mention_counts([skill.id]) == {skill.id: 1}

    def test_delete_mentions_for_source(self, sa_session):
        skill = SkillModel(name="Go", source="user")
        sa_session.add(skill)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        repo.upsert_mentions(skill.id, "job", "job-uuid-1")
        repo.upsert_mentions(skill.id, "job", "job-uuid-2")
        repo.delete_mentions_for_source("job", "job-uuid-1")

        assert repo.get_mention_counts([skill.id]) == {skill.id: 1}

    def test_mention_counts_empty_for_unknown_ids(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session)
        assert repo.get_mention_counts([]) == {}
        assert repo.get_mention_counts([9999]) == {}


class TestSkillAliases:
    def test_add_alias(self, sa_session):
        skill = SkillModel(name="React", source="user")
        sa_session.add(skill)
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        updated = repo.add_alias(skill.id, "ReactJS")
        assert updated is not None
        assert "ReactJS" in updated["aliases"]

    def test_add_alias_idempotent(self, sa_session):
        skill = SkillModel(name="React", source="user")
        sa_session.add(skill)
        sa_session.flush()
        sa_session.add(SkillAliasModel(skill_id=skill.id, alias_name="ReactJS", normalized_name="reactjs"))
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        updated = repo.add_alias(skill.id, "ReactJS")
        assert updated["aliases"].count("ReactJS") == 1
        assert sa_session.query(SkillAliasModel).count() == 1

    def test_add_alias_missing_skill(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session)
        assert repo.add_alias(9999, "ReactJS") is None

    def test_remove_alias(self, sa_session):
        skill = SkillModel(name="React", source="user")
        sa_session.add(skill)
        sa_session.flush()
        sa_session.add(SkillAliasModel(skill_id=skill.id, alias_name="ReactJS", normalized_name="reactjs"))
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        updated = repo.remove_alias(skill.id, "ReactJS")
        assert "ReactJS" not in updated["aliases"]
        assert sa_session.query(SkillAliasModel).count() == 0

    def test_remove_alias_missing_skill(self, sa_session):
        repo = SQLAlchemySkillRepository(sa_session)
        assert repo.remove_alias(9999, "ReactJS") is None


class TestMergeFoldsMentions:
    def test_merge_repoints_mentions(self, sa_session):
        target = SkillModel(name="React", source="user")
        source = SkillModel(name="ReactJS", source="user")
        sa_session.add_all([target, source])
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        repo.upsert_mentions(source.id, "job", "job-1")
        repo.upsert_mentions(source.id, "company", "company-1")

        result = repo.merge(target.id, [source.id])
        assert result["status"] == "merged"

        counts = repo.get_mention_counts([target.id, source.id])
        assert counts == {target.id: 2}
        rows = sa_session.query(SkillMentionModel).filter(SkillMentionModel.skill_id == target.id).all()
        assert {r.source_type for r in rows} == {"job", "company"}

    def test_merge_skips_duplicate_mention_keys(self, sa_session):
        target = SkillModel(name="React", source="user")
        source = SkillModel(name="ReactJS", source="user")
        sa_session.add_all([target, source])
        sa_session.commit()

        repo = SQLAlchemySkillRepository(sa_session)
        repo.upsert_mentions(target.id, "job", "job-1", status="matched")
        repo.upsert_mentions(source.id, "job", "job-1", status="low")

        repo.merge(target.id, [source.id])

        rows = sa_session.query(SkillMentionModel).filter(SkillMentionModel.skill_id == target.id).all()
        assert len(rows) == 1
        assert rows[0].status == "matched"
