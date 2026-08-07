"""SQLAlchemy candidate repository tests.

Uses the shared ``sa_session`` fixture (transaction-rolled-back Postgres test
DB) so commits inside repositories stay isolated per test.
"""

import pytest

from candidates.infrastructure import (
    SQLAlchemyCandidateRepository,
    SQLAlchemyCandidateProfileRepository,
    SQLAlchemyCandidateSourceRepository,
)
from skills.infrastructure import SQLAlchemySkillRepository


class TestCandidateRepository:
    def test_create_and_get_candidate(self, sa_session):
        repo = SQLAlchemyCandidateRepository(sa_session)
        created = repo.create_candidate({"name": "Hassan", "headline": "Backend Engineer"})
        assert created["id"]
        assert created["name"] == "Hassan"

        loaded = repo.get_candidate()
        assert loaded["id"] == created["id"]

    def test_get_candidate_none_when_empty(self, sa_session):
        repo = SQLAlchemyCandidateRepository(sa_session)
        assert repo.get_candidate() is None

    def test_update_candidate(self, sa_session):
        repo = SQLAlchemyCandidateRepository(sa_session)
        created = repo.create_candidate({"name": "Hassan"})
        updated = repo.update_candidate(created["id"], {"location": "Berlin"})
        assert updated["location"] == "Berlin"
        assert updated["name"] == "Hassan"

    def test_update_missing_candidate_returns_none(self, sa_session):
        repo = SQLAlchemyCandidateRepository(sa_session)
        assert repo.update_candidate("missing", {"name": "x"}) is None


class TestCandidateProfileRepository:
    def test_get_or_create_creates_singleton(self, sa_session):
        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        first = repo.get_or_create_current()
        second = repo.get_or_create_current()
        assert first["id"] == second["id"]
        assert first["version"] == 1
        assert first["candidate_id"]

    def test_get_current_profile_none_when_empty(self, sa_session):
        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        assert repo.get_current_profile() is None

    def test_get_current_profile_has_empty_children(self, sa_session):
        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = repo.get_or_create_current()
        current = repo.get_current_profile()
        assert current["id"] == profile["id"]
        for kind in ("skills", "experiences", "projects", "educations", "certificates", "interests", "languages"):
            assert current[kind] == []

    def test_update_core(self, sa_session):
        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = repo.get_or_create_current()
        updated = repo.update_core(profile["id"], {"version": 2, "title": "Staff Engineer"})
        assert updated["version"] == 2
        assert updated["title"] == "Staff Engineer"

    def test_skill_persistence_links_to_skill_skills(self, sa_session):
        skill_repo = SQLAlchemySkillRepository(sa_session)
        skill = skill_repo.create({"name": "Python", "level": 4, "category": "Technical"})

        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = repo.get_or_create_current()
        count = repo.replace_children(profile["id"], "skills", [{
            "name": "Python",
            "skill_id": skill["id"],
            "level": 4,
            "category": "Technical",
            "confidence": 0.96,
            "origin": "explicit",
            "evidence": {"sources": ["resume"], "confidence": 0.96, "notes": ""},
        }])
        assert count == 1

        current = repo.get_current_profile()
        assert len(current["skills"]) == 1
        stored = current["skills"][0]
        assert stored["name"] == "Python"
        assert stored["skill_id"] == skill["id"]
        assert stored["confidence"] == 0.96
        assert stored["evidence"]["sources"] == ["resume"]

    def test_replace_children_swaps_set(self, sa_session):
        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = repo.get_or_create_current()
        repo.replace_children(profile["id"], "interests", [{"name": "Kubernetes"}, {"name": "Rust"}])
        repo.replace_children(profile["id"], "interests", [{"name": "Go"}])

        current = repo.get_current_profile()
        assert [i["name"] for i in current["interests"]] == ["Go"]

    def test_replace_children_experiences_with_lists(self, sa_session):
        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = repo.get_or_create_current()
        repo.replace_children(profile["id"], "experiences", [{
            "company": "Acme",
            "role": "Backend Engineer",
            "highlights": ["built X", "shipped Y"],
            "skills": ["Python", "Docker"],
            "evidence": {"sources": ["resume"], "confidence": 0.9, "notes": ""},
        }])
        current = repo.get_current_profile()
        assert current["experiences"][0]["company"] == "Acme"
        assert current["experiences"][0]["highlights"] == ["built X", "shipped Y"]
        assert current["experiences"][0]["evidence"]["sources"] == ["resume"]

    def test_replace_children_unknown_kind_raises(self, sa_session):
        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = repo.get_or_create_current()
        with pytest.raises(ValueError):
            repo.replace_children(profile["id"], "pets", [])

    def test_create_and_list_versions(self, sa_session):
        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = repo.get_or_create_current()
        version = repo.create_version(
            profile["id"], 1, {"skills": []}, {"resume": 1}, change_summary="initial"
        )
        assert version["version"] == 1
        assert version["snapshot"] == {"skills": []}
        assert version["source_versions"] == {"resume": 1}

        versions = repo.list_versions(profile["id"])
        assert len(versions) == 1
        assert versions[0]["snapshot"] == {"skills": []}

    def test_list_versions_newest_first(self, sa_session):
        repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = repo.get_or_create_current()
        repo.create_version(profile["id"], 1, {}, {}, "v1")
        repo.create_version(profile["id"], 2, {}, {}, "v2")
        versions = repo.list_versions(profile["id"])
        assert [v["version"] for v in versions] == [2, 1]


class TestCandidateSourceRepository:
    def test_crud(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = profile_repo.get_or_create_current()
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)

        created = source_repo.create({
            "profile_id": profile["id"], "source_type": "resume", "version": 2, "status": "processed",
        })
        assert created["id"]
        assert created["status"] == "processed"

        assert source_repo.get_by_type_and_version(profile["id"], "resume", 2)["id"] == created["id"]
        assert source_repo.get_by_type_and_version(profile["id"], "resume", 3) is None

        listed = source_repo.list_for_profile(profile["id"])
        assert len(listed) == 1
        assert listed[0]["source_type"] == "resume"

        updated = source_repo.update(created["id"], {"status": "failed", "error": "boom"})
        assert updated["status"] == "failed"
        assert updated["error"] == "boom"

    def test_list_newest_first(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = profile_repo.get_or_create_current()
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        source_repo.create({"profile_id": profile["id"], "source_type": "linkedin", "version": 1})
        source_repo.create({"profile_id": profile["id"], "source_type": "resume", "version": 1})
        listed = source_repo.list_for_profile(profile["id"])
        assert [s["source_type"] for s in listed] == ["resume", "linkedin"]

    def test_update_missing_returns_none(self, sa_session):
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        assert source_repo.update("missing", {"status": "failed"}) is None

    def test_create_persists_raw_text(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = profile_repo.get_or_create_current()
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)

        created = source_repo.create({
            "profile_id": profile["id"],
            "source_type": "resume",
            "version": 1,
            "raw_text": "Some resume body",
            "status": "pending",
        })
        assert created["raw_text"] == "Some resume body"
        fetched = source_repo.get_by_type_and_version(profile["id"], "resume", 1)
        assert fetched["raw_text"] == "Some resume body"

    def test_update_can_change_raw_text(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = profile_repo.get_or_create_current()
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)

        created = source_repo.create({
            "profile_id": profile["id"], "source_type": "linkedin", "version": 1, "raw_text": "old",
        })
        updated = source_repo.update(created["id"], {"raw_text": "new", "status": "processed"})
        assert updated["raw_text"] == "new"
        assert updated["status"] == "processed"

    def test_get_latest_by_type_returns_highest_version(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = profile_repo.get_or_create_current()
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        source_repo.create({"profile_id": profile["id"], "source_type": "resume", "version": 1, "raw_text": "v1"})
        source_repo.create({"profile_id": profile["id"], "source_type": "resume", "version": 2, "raw_text": "v2"})
        source_repo.create({"profile_id": profile["id"], "source_type": "linkedin", "version": 3, "raw_text": "li"})

        latest = source_repo.get_latest_by_type(profile["id"], "resume")
        assert latest["version"] == 2
        assert latest["raw_text"] == "v2"

    def test_get_latest_by_type_none_when_missing(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = profile_repo.get_or_create_current()
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        assert source_repo.get_latest_by_type(profile["id"], "github") is None

    def test_get_next_version(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        profile = profile_repo.get_or_create_current()
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)

        assert source_repo.get_next_version(profile["id"], "resume") == 1
        source_repo.create({"profile_id": profile["id"], "source_type": "resume", "version": 1})
        source_repo.create({"profile_id": profile["id"], "source_type": "resume", "version": 2})
        assert source_repo.get_next_version(profile["id"], "resume") == 3
        assert source_repo.get_next_version(profile["id"], "linkedin") == 1
