"""Integration test: CandidateExtractService against real SQLAlchemy repos.

End-to-end check that the service's dict shapes round-trip through the real
mappers (candidate_skills, candidate_experiences, ...), the source row is
recorded, and skills resolve into the ``skill.skills`` vocabulary.
"""

import json
from types import SimpleNamespace

from candidates.application.adapters.resume_adapter import ResumeAdapter
from candidates.application.adapters.linkedin_adapter import LinkedInAdapter
from candidates.application.services.candidate_extract_service import (
    CandidateExtractService,
)
from candidates.infrastructure import (
    SQLAlchemyCandidateProfileRepository,
    SQLAlchemyCandidateSourceRepository,
)
from skills.infrastructure import SQLAlchemySkillRepository


class FakeLLM:
    def __init__(self, content):
        self.content = content
        self.calls = 0

    def generate_structured(self, prompt, schema=None, timeout=None):
        self.calls += 1
        return SimpleNamespace(content=self.content)


def _payload():
    return {
        "profile": {
            "name": "Hassan",
            "title": "Senior Backend Engineer",
            "headline": "Go + Python engineer",
            "summary": "8 years building distributed systems.",
            "location": "Cairo, Egypt",
        },
        "skills": [
            {"name": "Python", "level": 5, "category": "language", "years_of_experience": 8, "last_used": "2025", "confidence": 0.98},
            {"name": "PostgreSQL", "level": 4, "category": "database", "confidence": 0.9},
        ],
        "experiences": [
            {"company": "Acme", "role": "Backend Engineer", "start_date": "2020", "end_date": "2024", "duration_months": 48, "summary": "Built the payments platform.", "highlights": ["Reduced p99 by 40%"], "skills": ["Python", "PostgreSQL"], "confidence": 0.95}
        ],
        "projects": [{"name": "CLI tool", "description": "A dev CLI.", "url": "https://example.com", "role": "author", "skills": ["Go"], "start_date": "2023", "end_date": "2023", "confidence": 0.8}],
        "educations": [{"institution": "Cairo University", "degree": "BSc", "field": "CS", "start_date": "2010", "end_date": "2014", "confidence": 0.99}],
        "certificates": [{"name": "AWS SA", "issuer": "Amazon", "issue_date": "2022", "credential_url": "https://aws", "confidence": 0.9}],
        "interests": [{"name": "Open Source"}],
        "languages": [{"name": "Arabic", "proficiency": "native"}],
    }


def _seed_sources(sa_session, source_repo, profile_repo, rows):
    """Create the current profile and pending source rows to extract."""
    profile = profile_repo.get_or_create_current()
    for source_type, version, raw_text in rows:
        source_repo.create(
            {
                "profile_id": profile["id"],
                "source_type": source_type,
                "version": version,
                "raw_text": raw_text,
                "status": "pending",
            }
        )
    return profile


def _resume_adapter(source_repo, profile_id):
    return ResumeAdapter(source_repo, profile_id)


class TestExtractServiceIntegration:
    def test_full_round_trip(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        skill_repo = SQLAlchemySkillRepository(sa_session)

        profile = _seed_sources(sa_session, source_repo, profile_repo, [("resume", 1, "My resume text")])

        service = CandidateExtractService(
            profile_repo=profile_repo,
            source_repo=source_repo,
            skill_repo=skill_repo,
            llm=FakeLLM(content=json.dumps(_payload())),
        )
        result = service.process(_resume_adapter(source_repo, profile["id"]))

        assert result["status"] == "processed"
        assert result["source_type"] == "resume"
        assert result["version"] == 1
        assert result["skill_count"] == 2
        assert result["prompt_version"]

        current = profile_repo.get_current_profile()
        assert current["name"] == "Hassan"
        assert current["title"] == "Senior Backend Engineer"
        assert current["location"] == "Cairo, Egypt"

        stored_skills = current["skills"]
        assert len(stored_skills) == 2
        names = [s["name"] for s in stored_skills]
        assert set(names) == {"Python", "PostgreSQL"}
        python = next(s for s in stored_skills if s["name"] == "Python")
        assert python["skill_id"] is not None
        assert python["origin"] == "explicit"
        assert python["confidence"] == 0.98
        assert python["evidence"]["sources"] == ["resume v1"]

        assert current["experiences"][0]["company"] == "Acme"
        assert current["experiences"][0]["highlights"] == ["Reduced p99 by 40%"]
        assert current["projects"][0]["name"] == "CLI tool"
        assert current["educations"][0]["institution"] == "Cairo University"
        assert current["certificates"][0]["name"] == "AWS SA"
        assert current["interests"][0]["name"] == "Open Source"
        assert current["languages"][0]["proficiency"] == "native"

        source = source_repo.get_by_type_and_version(current["id"], "resume", 1)
        assert source is not None
        assert source["status"] == "processed"
        assert source["processed_at"]

    def test_reprocess_same_version_extracts_again(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        skill_repo = SQLAlchemySkillRepository(sa_session)

        profile = _seed_sources(sa_session, source_repo, profile_repo, [("resume", 1, "My resume text")])

        service = CandidateExtractService(
            profile_repo=profile_repo,
            source_repo=source_repo,
            skill_repo=skill_repo,
            llm=FakeLLM(content=json.dumps(_payload())),
        )
        first = service.process(_resume_adapter(source_repo, profile["id"]))
        second = service.process(_resume_adapter(source_repo, profile["id"]))

        assert first["status"] == "processed"
        assert second["status"] == "processed"

    def test_first_merge_persists_version_v1_snapshot(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        skill_repo = SQLAlchemySkillRepository(sa_session)

        profile = _seed_sources(sa_session, source_repo, profile_repo, [("resume", 1, "My resume text")])

        service = CandidateExtractService(
            profile_repo=profile_repo,
            source_repo=source_repo,
            skill_repo=skill_repo,
            llm=FakeLLM(content=json.dumps(_payload())),
        )
        service.process(_resume_adapter(source_repo, profile["id"]))

        profile = profile_repo.get_current_profile()
        versions = profile_repo.list_versions(profile["id"])
        assert len(versions) == 1
        assert versions[0]["version"] == 1
        assert versions[0]["source_versions"] == {"resume": 1}
        assert versions[0]["snapshot"]["name"] == "Hassan"
        assert profile["version"] == 1

    def test_second_source_bumps_version_to_v2(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        skill_repo = SQLAlchemySkillRepository(sa_session)

        profile = _seed_sources(
            sa_session,
            source_repo,
            profile_repo,
            [("resume", 1, "My resume text"), ("linkedin", 1, "LinkedIn profile")],
        )

        service = CandidateExtractService(
            profile_repo=profile_repo,
            source_repo=source_repo,
            skill_repo=skill_repo,
            llm=FakeLLM(content=json.dumps(_payload())),
        )
        service.process(_resume_adapter(source_repo, profile["id"]))
        service.process(LinkedInAdapter(source_repo, profile["id"]))

        profile = profile_repo.get_current_profile()
        versions = profile_repo.list_versions(profile["id"])
        assert len(versions) == 2
        assert versions[0]["version"] == 2
        assert versions[0]["source_versions"] == {"linkedin": 1}
        assert profile["version"] == 2

    def test_domain_events_collected_integration(self, sa_session):
        profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        skill_repo = SQLAlchemySkillRepository(sa_session)

        profile = _seed_sources(sa_session, source_repo, profile_repo, [("resume", 1, "My resume text")])

        service = CandidateExtractService(
            profile_repo=profile_repo,
            source_repo=source_repo,
            skill_repo=skill_repo,
            llm=FakeLLM(content=json.dumps(_payload())),
        )
        service.process(_resume_adapter(source_repo, profile["id"]))

        types = {e.event_type for e in service.event_publisher.events}
        assert "candidate.profile.updated" in types
        assert "candidate.source.updated" in types
        assert "candidate.merge.completed" in types
        assert "candidate.version.created" in types
        assert "candidate.skill.inferred" in types
