"""Candidate domain entity tests."""

from candidates.domain.entities import (
    Candidate,
    CandidateProfile,
    CandidateSource,
    CandidateSkill,
    CandidateExperience,
    CandidateProject,
    CandidateEducation,
    CandidateCertificate,
    CandidateInterest,
    CandidateLanguage,
    CandidateProfileVersion,
)
from candidates.domain.value_objects.evidence import Evidence, Confidence


class TestValueObjects:
    def test_confidence_clamps_low(self):
        assert Confidence(-0.2).value == 0.0

    def test_confidence_clamps_high(self):
        assert Confidence(1.5).value == 1.0

    def test_confidence_roundtrip(self):
        assert Confidence(0.96).value == 0.96

    def test_evidence_defaults(self):
        evidence = Evidence()
        assert evidence.sources == []
        assert evidence.confidence == 0.0
        assert evidence.notes == ""

    def test_evidence_clamps_confidence(self):
        assert Evidence(sources=["resume"], confidence=1.5).confidence == 1.0

    def test_evidence_round_trip(self):
        evidence = Evidence(sources=["resume", "linkedin"], confidence=0.96, notes="multi-source")
        assert Evidence.from_dict(evidence.to_dict()) == evidence

    def test_evidence_from_dict_none(self):
        assert Evidence.from_dict(None) == Evidence()


class TestCandidate:
    def test_round_trip(self):
        candidate = Candidate(name="Hassan", headline="Senior Backend Engineer", summary="Python", location="Berlin")
        assert Candidate.from_dict(candidate.to_dict()).to_dict() == candidate.to_dict()

    def test_defaults(self):
        assert Candidate().name == ""
        assert Candidate().id


class TestCandidateProfile:
    def test_round_trip(self):
        profile = CandidateProfile(
            candidate_id="c1", version=3, name="Hassan", title="Backend Engineer",
            headline="Building platforms", summary="summary", location="Berlin",
        )
        assert CandidateProfile.from_dict(profile.to_dict()).to_dict() == profile.to_dict()

    def test_default_version(self):
        assert CandidateProfile(candidate_id="c1").version == 1


class TestCandidateSource:
    def test_round_trip(self):
        source = CandidateSource(profile_id="p1", source_type="linkedin", version=3, status="processed")
        assert CandidateSource.from_dict(source.to_dict()).to_dict() == source.to_dict()

    def test_defaults(self):
        source = CandidateSource(profile_id="p1", source_type="resume")
        assert source.version == 1
        assert source.status == "pending"

    def test_invalid_status_returns_pending(self):
        assert CandidateSource(profile_id="p1", source_type="resume", status="bogus").status == "pending"


class TestCandidateSkill:
    def test_round_trip(self):
        skill = CandidateSkill(
            profile_id="p1", skill_id=42, name="Python", level=4, category="Technical",
            evidence=Evidence(sources=["resume", "linkedin"], confidence=0.96),
            origin="explicit", years_of_experience=6.5, last_used="2026",
        )
        assert CandidateSkill.from_dict(skill.to_dict()).to_dict() == skill.to_dict()

    def test_confidence_clamped(self):
        skill = CandidateSkill(name="Docker", confidence=2.0)
        assert skill.confidence == 1.0

    def test_default_origin_explicit(self):
        assert CandidateSkill(name="Python").origin == "explicit"

    def test_confidence_in_evidence_and_top_level(self):
        skill = CandidateSkill(name="FastAPI", evidence=Evidence(confidence=0.9))
        assert skill.to_dict()["confidence"] == 0.9
        assert skill.to_dict()["evidence"]["confidence"] == 0.9


class TestCandidateExperience:
    def test_round_trip(self):
        exp = CandidateExperience(
            profile_id="p1", company="Acme", role="Backend Engineer",
            start_date="2021-01", end_date="2024-12", duration_months=47,
            summary="built APIs", highlights=["a", "b"], skills=["Python", "FastAPI"],
            evidence=Evidence(sources=["resume"], confidence=0.98),
        )
        assert CandidateExperience.from_dict(exp.to_dict()).to_dict() == exp.to_dict()

    def test_list_defaults(self):
        assert CandidateExperience().highlights == []
        assert CandidateExperience().skills == []


class TestCandidateProject:
    def test_round_trip(self):
        project = CandidateProject(
            profile_id="p1", name="Job Search Intelligence", description="AI platform",
            url="https://github.com/x", role="owner", skills=["LangGraph"],
            evidence=Evidence(sources=["github"], confidence=0.8),
        )
        assert CandidateProject.from_dict(project.to_dict()).to_dict() == project.to_dict()


class TestCandidateEducation:
    def test_round_trip(self):
        edu = CandidateEducation(
            profile_id="p1", institution="TU Berlin", degree="MSc", field="CS",
            evidence=Evidence(sources=["resume"], confidence=0.99),
        )
        assert CandidateEducation.from_dict(edu.to_dict()).to_dict() == edu.to_dict()


class TestCandidateCertificate:
    def test_round_trip(self):
        cert = CandidateCertificate(
            profile_id="p1", name="CKA", issuer="CNCF", issue_date="2024",
            credential_url="https://example.com/cert",
            evidence=Evidence(sources=["linkedin"], confidence=0.7),
        )
        assert CandidateCertificate.from_dict(cert.to_dict()).to_dict() == cert.to_dict()


class TestCandidateInterest:
    def test_round_trip(self):
        interest = CandidateInterest(profile_id="p1", name="Kubernetes")
        assert CandidateInterest.from_dict(interest.to_dict()).to_dict() == interest.to_dict()


class TestCandidateLanguage:
    def test_round_trip(self):
        lang = CandidateLanguage(profile_id="p1", name="English", proficiency="native")
        assert CandidateLanguage.from_dict(lang.to_dict()).to_dict() == lang.to_dict()

    def test_invalid_proficiency_cleared(self):
        assert CandidateLanguage(name="German", proficiency="bogus").proficiency == ""


class TestCandidateProfileVersion:
    def test_round_trip(self):
        version = CandidateProfileVersion(
            profile_id="p1", version=3, snapshot={"name": "Hassan"},
            source_versions={"resume": 2, "linkedin": 1}, change_summary="merged resume v2",
        )
        assert CandidateProfileVersion.from_dict(version.to_dict()).to_dict() == version.to_dict()

    def test_dict_defaults(self):
        version = CandidateProfileVersion(profile_id="p1")
        assert version.snapshot == {}
        assert version.source_versions == {}
