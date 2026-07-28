"""Tests for the Prompt Management Platform.

Covers: rendering, variables, missing inputs, structured output, regression, golden output.
"""

from __future__ import annotations

import pytest

from ai.infrastructure.prompts.base import PromptSpec, PromptType
from ai.infrastructure.prompts.inputs import (
    CareerInsightsInput,
    CompanyAnalysisInput,
    CompanyExtractionInput,
    CoverLetterInput,
    JobExtractionInput,
    JobScoreInput,
    JobSummaryInput,
    ResumeTailorInput,
    RoadmapInput,
    SkillExtractionInput,
)
from ai.infrastructure.prompts.observability import PromptLogger, get_prompt_logger, reset_prompt_logger
from ai.infrastructure.prompts.registry import PromptRegistry, get_prompt, get_registry, register_prompt, reset_registry
from ai.infrastructure.prompts.register_all import register_all_prompts
from ai.infrastructure.prompts.template import PromptTemplate


@pytest.fixture(autouse=True)
def clean_registry():
    """Reset registry before each test."""
    reset_registry()
    reset_prompt_logger()
    register_all_prompts()
    yield
    reset_registry()
    reset_prompt_logger()


class TestPromptRegistry:
    def test_registry_holds_all_prompts(self):
        registry = get_registry()
        ids = registry.list_identifiers()
        assert "job.extract" in ids
        assert "job.score" in ids
        assert "job.summary" in ids
        assert "company.extract" in ids
        assert "company.analyze" in ids
        assert "resume.tailor" in ids
        assert "resume.cover-letter" in ids
        assert "skills.extract" in ids
        assert "skills.roadmap" in ids
        assert "insights.overview" in ids

    def test_get_nonexistent_prompt_raises(self):
        registry = get_registry()
        with pytest.raises(KeyError):
            registry.get("nonexistent.prompt")

    def test_get_nonexistent_version_raises(self):
        registry = get_registry()
        with pytest.raises(KeyError):
            registry.get("job.extract", version="99.99.99")

    def test_versioning(self):
        registry = get_registry()
        spec = registry.get_spec("job.extract")
        assert spec.version == "1.0.0"

        registry.create_version(
            identifier="job.extract",
            template="New template {content}",
            version="2.0.0",
            description="Major revision",
        )
        spec = registry.get_spec("job.extract")
        assert spec.version == "2.0.0"

        spec_v1 = registry.get_spec("job.extract", version="1.0.0")
        assert spec_v1.version == "1.0.0"

    def test_list_versions(self):
        registry = get_registry()
        registry.create_version(
            identifier="job.extract",
            template="New {content}",
            version="1.1.0",
            description="Minor update",
        )
        versions = registry.list_versions("job.extract")
        assert "1.0.0" in versions
        assert "1.1.0" in versions

    def test_list_by_owner(self):
        registry = get_registry()
        job_prompts = registry.list_by_owner("jobs")
        identifiers = [p.identifier for p in job_prompts]
        assert "job.extract" in identifiers
        assert "job.score" in identifiers

    def test_list_by_tags(self):
        registry = get_registry()
        extraction_prompts = registry.list_by_tags(["extraction"])
        for p in extraction_prompts:
            assert "extraction" in p.tags

    def test_deregister(self):
        registry = get_registry()
        registry.deregister("job.score")
        assert not registry.exists("job.score")

    def test_deregister_specific_version(self):
        registry = get_registry()
        registry.create_version(
            identifier="job.extract",
            template="New {content}",
            version="1.1.0",
            description="Update",
        )
        registry.deregister("job.extract", version="1.0.0")
        assert registry.exists("job.extract")
        assert not registry.exists("job.extract", version="1.0.0")

    def test_register_and_get_custom_prompt(self):
        prompt = register_prompt(
            identifier="test.custom",
            template="Hello {name}!",
            owner="tests",
            description="A test prompt",
        )
        assert prompt.identifier == "test.custom"
        assert prompt.version == "1.0.0"

        result = get_prompt("test.custom", name="World")
        assert "Hello World!" in result


class TestPromptRendering:
    def test_job_extraction_renders(self):
        result = get_prompt("job.extract", content="Software Engineer at Google")
        assert "Software Engineer at Google" in result
        assert "JSON format" in result

    def test_job_score_renders_with_minimal_fields(self):
        result = get_prompt(
            "job.score",
            title="Engineer",
            user_skills="Python",
            user_experience="5 years",
        )
        assert "Engineer" in result
        assert "Fit Score" in result

    def test_job_score_renders_with_all_fields(self):
        result = get_prompt(
            "job.score",
            title="Senior Engineer",
            company="Google",
            location="Berlin",
            stack="Python, Go",
            description="Backend role",
            user_skills="Python, Go",
            user_experience="8 years",
            user_preferences="Remote, Visa sponsorship",
        )
        assert "Senior Engineer" in result
        assert "Berlin" in result
        assert "Remote" in result

    def test_job_summary_renders(self):
        result = get_prompt(
            "job.summary",
            title="DevOps Engineer",
            company="AWS",
            description="Cloud infrastructure role",
        )
        assert "DevOps Engineer" in result
        assert "AWS" in result
        assert "Key Responsibilities" in result

    def test_company_extraction_renders(self):
        result = get_prompt("company.extract", content="Microsoft is a technology company")
        assert "Microsoft" in result
        assert "company_type" in result

    def test_company_analysis_renders(self):
        result = get_prompt(
            "company.analyze",
            name="Google",
            industry="Technology",
            tech_stack="Python, Go, Kubernetes",
        )
        assert "Google" in result
        assert "Fit Score" in result

    def test_resume_tailor_renders(self):
        result = get_prompt(
            "resume.tailor",
            job_title="Backend Engineer",
            job_company="Spotify",
            resume_text="Experienced Python developer",
        )
        assert "Backend Engineer" in result
        assert "Spotify" in result

    def test_cover_letter_renders(self):
        result = get_prompt(
            "resume.cover-letter",
            job_title="Frontend Engineer",
            job_company="Stripe",
            resume_text="React developer with 5 years experience",
        )
        assert "Frontend Engineer" in result
        assert "Stripe" in result
        assert "cover letter" in result.lower()

    def test_skill_extraction_renders(self):
        result = get_prompt("skills.extract", job_data="Python, Go, Kubernetes jobs")
        assert "programming_languages" in result
        assert "categorize" in result.lower()

    def test_roadmap_renders(self):
        result = get_prompt(
            "skills.roadmap",
            current_skills="Python, JavaScript",
            market_demand="Go, Rust, Kubernetes",
        )
        assert "learning roadmap" in result.lower()
        assert "priority" in result

    def test_career_insights_renders(self):
        result = get_prompt(
            "insights.overview",
            job_count="45",
            skill_count="120",
            health_score="78",
        )
        assert "45" in result
        assert "120" in result
        assert "78" in result
        assert "Career Health" in result


class TestTypedInputModels:
    def test_job_extraction_input(self):
        inp = JobExtractionInput(content="Software Engineer role")
        assert inp.content == "Software Engineer role"

    def test_job_extraction_input_empty_raises(self):
        with pytest.raises(ValueError):
            JobExtractionInput(content="")

    def test_job_score_input(self):
        inp = JobScoreInput(
            title="Engineer",
            company="Google",
            user_skills="Python",
            user_experience="5 years",
        )
        assert inp.title == "Engineer"
        d = inp.model_dump()
        result = get_prompt("job.score", **d)
        assert "Engineer" in result

    def test_job_summary_input(self):
        inp = JobSummaryInput(title="Engineer", company="Google")
        d = inp.model_dump()
        result = get_prompt("job.summary", **d)
        assert "Google" in result

    def test_company_extraction_input(self):
        inp = CompanyExtractionInput(content="Company data here")
        d = inp.model_dump()
        result = get_prompt("company.extract", **d)
        assert "Company data here" in result

    def test_company_analysis_input(self):
        inp = CompanyAnalysisInput(name="Microsoft", tech_stack="Azure")
        d = inp.model_dump()
        result = get_prompt("company.analyze", **d)
        assert "Microsoft" in result

    def test_resume_tailor_input(self):
        inp = ResumeTailorInput(job_title="Engineer", job_company="Meta", resume_text="Worked on...")
        d = inp.model_dump()
        result = get_prompt("resume.tailor", **d)
        assert "Meta" in result

    def test_cover_letter_input(self):
        inp = CoverLetterInput(job_title="Engineer", job_company="Meta", resume_text="Experienced")
        d = inp.model_dump()
        result = get_prompt("resume.cover-letter", **d)
        assert "Meta" in result

    def test_skill_extraction_input(self):
        inp = SkillExtractionInput(job_data="Python, Go jobs")
        d = inp.model_dump()
        result = get_prompt("skills.extract", **d)
        assert "Python, Go jobs" in result

    def test_roadmap_input(self):
        inp = RoadmapInput(current_skills="Python", market_demand="Go")
        d = inp.model_dump()
        result = get_prompt("skills.roadmap", **d)
        assert "Python" in result

    def test_career_insights_input(self):
        inp = CareerInsightsInput(job_count="10", skill_count="50", health_score="85")
        d = inp.model_dump()
        result = get_prompt("insights.overview", **d)
        assert "85" in result


class TestPromptRenderingEdgeCases:
    def test_empty_variables_renders(self):
        result = get_prompt("job.score")
        assert result is not None
        assert len(result) > 0

    def test_partial_variables(self):
        result = get_prompt("job.score", title="Test")
        assert "Test" in result
        assert "Fit Score (0-100)" in result

    def test_unknown_variables_ignored(self):
        result = get_prompt("job.extract", content="Test", unknown_var="ignored")
        assert "Test" in result

    def test_special_characters_in_variables(self):
        result = get_prompt(
            "job.extract",
            content="C++ & Rust developer with 10+ years experience at $BIG_CO",
        )
        assert "C++" in result

    def test_unicode_content(self):
        content = "Senior Software Engineer (m/w/d) — München"
        result = get_prompt("job.extract", content=content)
        assert "München" in result

    def test_large_content(self):
        content = "A" * 100_000
        result = get_prompt("job.extract", content=content)
        assert len(result) > len(content) * 0.9


class TestPromptTypeEnum:
    def test_all_types(self):
        assert PromptType.SYSTEM.value == "system"
        assert PromptType.DEVELOPER.value == "developer"
        assert PromptType.USER.value == "user"
        assert PromptType.TOOL.value == "tool"
        assert PromptType.EXTRACTION.value == "extraction"
        assert PromptType.VALIDATION.value == "validation"
        assert PromptType.REPAIR.value == "repair"
        assert PromptType.SUMMARIZATION.value == "summarization"
        assert PromptType.CLASSIFICATION.value == "classification"
        assert PromptType.EVALUATION.value == "evaluation"
        assert PromptType.REFLECTION.value == "reflection"

    def test_prompt_types_assigned_correctly(self):
        registry = get_registry()
        extraction_ids = [p.identifier for p in registry.list_by_tags(["extraction"])]
        for ident in extraction_ids:
            spec = registry.get_spec(ident)
            assert spec.prompt_type in (PromptType.EXTRACTION,)


class TestPromptObservability:
    def test_logger_tracks_renders(self):
        logger = get_prompt_logger()
        before = logger.render_count
        get_prompt("job.extract", content="Test")
        assert logger.render_count == before + 1

    def test_logger_tracks_executions(self):
        logger = get_prompt_logger()
        logger.log_execution(
            identifier="job.extract",
            version="1.0.0",
            provider="test",
            success=True,
        )
        assert len(logger.logs) == 1
        entry = logger.logs[0]
        assert entry.identifier == "job.extract"
        assert entry.success

    def test_logger_tracks_failures(self):
        logger = get_prompt_logger()
        logger.log_execution(
            identifier="job.score",
            version="1.0.0",
            provider="test",
            success=False,
            error="LLM timeout",
        )
        entry = logger.logs[0]
        assert not entry.success
        assert entry.error == "LLM timeout"

    def test_logger_clear(self):
        logger = get_prompt_logger()
        logger.log_execution(identifier="test", version="1.0.0")
        assert len(logger.logs) == 1
        logger.clear()
        assert len(logger.logs) == 0
        assert logger.render_count == 0


class TestPromptSpec:
    def test_spec_creation(self):
        spec = PromptSpec(
            identifier="test.prompt",
            version="1.0.0",
            description="Test",
            owner="tests",
            prompt_type=PromptType.SYSTEM,
        )
        assert spec.identifier == "test.prompt"
        assert spec.version == "1.0.0"

    def test_spec_defaults(self):
        spec = PromptSpec(identifier="test.id", owner="tests")
        assert spec.version == "1.0.0"
        assert spec.prompt_type == PromptType.SYSTEM
        assert spec.supported_providers == ["any"]
        assert spec.tags == []


class TestPromptTemplateConstruction:
    def test_from_string(self):
        template = PromptTemplate.from_string(
            template="Hello {name}!",
            identifier="test.hello",
            owner="tests",
        )
        result = template.render(name="World")
        assert "Hello World!" in result

    def test_from_messages(self):
        template = PromptTemplate.from_messages(
            messages=[("system", "You are a {role}"), ("user", "{input}")],
            identifier="test.chat",
            owner="tests",
        )
        result = template.render(role="helper", input="Help me")
        assert "SYSTEM" in result
        assert "helper" in result
        assert "Help me" in result

    def test_render_messages(self):
        template = PromptTemplate.from_string(
            template="Hello {name}",
            identifier="test.hello",
            owner="tests",
        )
        msgs = template.render_messages(name="World")
        assert len(msgs) == 1
        assert msgs[0]["role"] in ("human", "system")

    def test_input_variables(self):
        template = PromptTemplate.from_string(
            template="{a} and {b}",
            identifier="test.vars",
            owner="tests",
        )
        assert "a" in template.input_variables
        assert "b" in template.input_variables


class TestReusableComponents:
    def test_tone_instructions_exist(self):
        from ai.infrastructure.prompts.components import tone_instructions
        tmpl = tone_instructions("professional")
        assert tmpl is not None

    def test_tone_invalid_falls_back(self):
        from ai.infrastructure.prompts.components import tone_instructions
        tmpl = tone_instructions("nonexistent_tone")
        msg = tmpl.format()
        assert "professional" in msg.content

    def test_formatting_rules_exist(self):
        from ai.infrastructure.prompts.components import FORMATTING_RULES
        msg = FORMATTING_RULES.format()
        assert "section headers" in msg.content

    def test_json_rules_exist(self):
        from ai.infrastructure.prompts.components import JSON_RULES
        msg = JSON_RULES.format()
        assert "valid JSON" in msg.content


class TestGoldenOutput:
    def test_golden_job_extraction(self):
        content = "Senior Python Developer at Google, Mountain View. Salary: $150k-$200k."
        import hashlib
        result = get_prompt("job.extract", content=content)
        assert "Senior Python Developer" in result
        assert "Google" in result
        assert "$150k-$200k" in result


class TestPromptTemplatePartialVars:
    def test_partial_variable_handling(self):
        template = PromptTemplate.from_string(
            template="Fixed: {fixed_var}, Dynamic: {dynamic_var}",
            identifier="test.partial",
            owner="tests",
        )
        result = template.render(dynamic_var="hello")
        assert "Fixed: " in result
        assert "Dynamic: hello" in result
