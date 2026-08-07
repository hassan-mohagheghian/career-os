"""Tests for the candidate.extract prompt builder + output schema."""

import json

from candidates.application.services.candidate_extract_prompt import (
    CANDIDATE_EXTRACT_PROMPT_VERSION,
    CANDIDATE_EXTRACT_SCHEMA_VERSION,
    build_candidate_extract_output_schema,
    build_candidate_extract_prompt,
)


class TestVersionConstants:
    def test_versions_are_semver(self):
        assert len(CANDIDATE_EXTRACT_PROMPT_VERSION.split(".")) == 3
        assert len(CANDIDATE_EXTRACT_SCHEMA_VERSION.split(".")) == 3


class TestOutputSchema:
    def _schema(self):
        return build_candidate_extract_output_schema()

    def test_is_json_schema_object(self):
        schema = self._schema()
        assert schema["type"] == "object"
        props = schema["properties"]
        for section in (
            "profile",
            "skills",
            "experiences",
            "projects",
            "educations",
            "certificates",
            "interests",
            "languages",
        ):
            assert section in props
        for section in (
            "skills",
            "experiences",
            "projects",
            "educations",
            "certificates",
            "interests",
            "languages",
        ):
            assert props[section]["type"] == "array"

    def test_required_sections_present(self):
        schema = self._schema()
        for section in (
            "profile",
            "skills",
            "experiences",
            "projects",
            "educations",
            "certificates",
            "interests",
            "languages",
        ):
            assert section in schema["required"]

    def test_skill_item_fields(self):
        item = self._schema()["properties"]["skills"]["items"]["properties"]
        for field in ("name", "level", "category", "years_of_experience", "last_used", "confidence"):
            assert field in item
        assert item["level"]["minimum"] == 0
        assert item["level"]["maximum"] == 5
        assert item["confidence"]["maximum"] == 1.0

    def test_experience_item_fields(self):
        item = self._schema()["properties"]["experiences"]["items"]["properties"]
        for field in ("company", "role", "start_date", "end_date", "duration_months", "summary", "highlights", "skills", "confidence"):
            assert field in item

    def test_schema_is_valid_json_schema_parseable(self):
        # The schema itself must be serializable so it can be embedded in the prompt.
        json.dumps(self._schema())


class TestPromptBuilder:
    def test_embeds_source_label_and_schema(self):
        prompt = build_candidate_extract_prompt("resume", "My raw resume text")
        assert "resume" in prompt
        assert "My raw resume text" in prompt
        assert "Respond ONLY with valid JSON" in prompt
        # The JSON schema is embedded verbatim.
        assert json.dumps(build_candidate_extract_output_schema(), indent=2) in prompt

    def test_marks_source_type(self):
        linkedin_prompt = build_candidate_extract_prompt("linkedin", "li text")
        assert "LINKEDIN" in linkedin_prompt
