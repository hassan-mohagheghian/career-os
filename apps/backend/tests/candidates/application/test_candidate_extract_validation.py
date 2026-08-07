"""Tests for strict validation of the candidate.extract LLM output."""

import pytest
from pydantic import ValidationError

from candidates.application.services.candidate_extract_validation import (
    CandidateExtractOutput,
)


def _valid_payload(**overrides):
    payload = {
        "profile": {
            "name": "Hassan",
            "title": "Senior Backend Engineer",
            "headline": "Go + Python engineer",
            "summary": "8 years building distributed systems.",
            "location": "Cairo, Egypt",
        },
        "skills": [
            {
                "name": "Python",
                "level": 5,
                "category": "language",
                "years_of_experience": 8,
                "last_used": "2025",
                "confidence": 0.98,
            },
            {
                "name": "Kubernetes",
                "level": 4,
                "category": "infrastructure",
                "confidence": 0.9,
            },
        ],
        "experiences": [
            {
                "company": "Acme",
                "role": "Backend Engineer",
                "start_date": "2020",
                "end_date": "2024",
                "duration_months": 48,
                "summary": "Built payment platform.",
                "highlights": ["Reduced p99 by 40%"],
                "skills": ["Python", "PostgreSQL"],
                "confidence": 0.95,
            }
        ],
        "projects": [
            {"name": "Open source CLI", "description": "A CLI tool.", "url": "https://x", "role": "author", "skills": ["Go"], "start_date": "2023", "end_date": "2023", "confidence": 0.8}
        ],
        "educations": [{"institution": "Cairo University", "degree": "BSc", "field": "CS", "start_date": "2010", "end_date": "2014", "confidence": 0.99}],
        "certificates": [{"name": "AWS SA", "issuer": "Amazon", "issue_date": "2022", "credential_url": "https://aws", "confidence": 0.9}],
        "interests": [{"name": "Open Source"}],
        "languages": [{"name": "Arabic", "proficiency": "native"}, {"name": "English", "proficiency": "fluent"}],
    }
    payload.update(overrides)
    return payload


class TestValidPayload:
    def test_valid_payload_parses(self):
        out = CandidateExtractOutput.model_validate(_valid_payload())
        assert out.profile.name == "Hassan"
        assert len(out.skills) == 2
        assert len(out.experiences) == 1
        assert len(out.projects) == 1
        assert len(out.educations) == 1
        assert len(out.certificates) == 1
        assert len(out.interests) == 1
        assert len(out.languages) == 2

    def test_empty_sections_default_to_empty_lists(self):
        out = CandidateExtractOutput.model_validate({"profile": {"name": "x"}, "skills": [], "experiences": [], "projects": [], "educations": [], "certificates": [], "interests": [], "languages": []})
        assert out.skills == []
        assert out.experiences == []
        assert out.languages == []

    def test_dump_payload_round_trip(self):
        payload = _valid_payload()
        out = CandidateExtractOutput.model_validate(payload)
        dumped = out.dump_payload()
        assert dumped["profile"]["name"] == "Hassan"
        assert dumped["skills"][0]["name"] == "Python"
        assert dumped["experiences"][0]["company"] == "Acme"


class TestCoercion:
    def test_confidence_clamped(self):
        out = CandidateExtractOutput.model_validate(_valid_payload(skills=[{"name": "X", "confidence": 5.0}]))
        assert out.skills[0].confidence == 1.0
        out2 = CandidateExtractOutput.model_validate(_valid_payload(skills=[{"name": "X", "confidence": -1}]))
        assert out2.skills[0].confidence == 0.0

    def test_confidence_string_coerced(self):
        out = CandidateExtractOutput.model_validate(_valid_payload(skills=[{"name": "X", "confidence": "0.5"}]))
        assert out.skills[0].confidence == 0.5

    def test_level_clamped(self):
        out = CandidateExtractOutput.model_validate(_valid_payload(skills=[{"name": "X", "level": 99}]))
        assert out.skills[0].level == 5
        out2 = CandidateExtractOutput.model_validate(_valid_payload(skills=[{"name": "X", "level": -3}]))
        assert out2.skills[0].level == 0

    def test_highlights_string_list_coerced(self):
        out = CandidateExtractOutput.model_validate(_valid_payload(experiences=[{"company": "A", "role": "r", "highlights": "one, two"}]))
        assert out.experiences[0].highlights == ["one", "two"]

    def test_proficiency_normalized(self):
        out = CandidateExtractOutput.model_validate(_valid_payload(languages=[{"name": "Fr", "proficiency": "NATIVE"}, {"name": "De", "proficiency": "bogus"}]))
        assert out.languages[0].proficiency == "native"
        assert out.languages[1].proficiency == ""


class TestRejection:
    def test_missing_skills_field_ok_when_provided_empty(self):
        # skills key present but null → coerced to []
        out = CandidateExtractOutput.model_validate(_valid_payload(skills=None))
        assert out.skills == []

    def test_skills_null_item_removed(self):
        out = CandidateExtractOutput.model_validate(_valid_payload(skills=[{"name": "Python"}, None, {"name": ""}]))
        assert [s.name for s in out.skills] == ["Python"]

    def test_invalid_types_rejected(self):
        with pytest.raises(ValidationError):
            CandidateExtractOutput.model_validate(_valid_payload(skills="not-a-list"))
