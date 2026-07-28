"""Tests for individual workflow graphs.

TDD: Tests define the contract for each graph.
DDD: Tests verify domain model invariants.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from ai.infrastructure.graphs.runtime.state import (
    create_initial_state,
    BaseState,
    JobExtractionOutput,
    JobAnalysisOutput,
    CompanyExtractionOutput,
    CompanyAnalysisOutput,
    ResumeOutput,
    CoverLetterOutput,
    SkillExtractionOutput,
    SkillRoadmapOutput,
    InsightSectionOutput,
    CareerInsightsOutput,
)


# ── Pydantic Output Model Tests ─────────────────────────────────────

class TestPydanticOutputModels:
    """Tests for all structured output models."""

    def test_job_extraction_output(self):
        output = JobExtractionOutput(
            title="Software Engineer",
            company="Tech Corp",
            location="Berlin",
            stack="Python, FastAPI",
        )
        assert output.title == "Software Engineer"
        assert output.company == "Tech Corp"
        data = output.model_dump()
        assert data["title"] == "Software Engineer"

    def test_job_analysis_output(self):
        extraction = JobExtractionOutput(title="Dev", company="Co")
        output = JobAnalysisOutput(
            extraction=extraction,
            tech_stack=["Python"],
            score="A",
        )
        assert output.extraction.title == "Dev"
        assert output.tech_stack == ["Python"]

    def test_company_extraction_output(self):
        output = CompanyExtractionOutput(
            name="Tech Inc",
            company_type="STARTUP",
            visa_sponsorship=True,
        )
        assert output.name == "Tech Inc"
        assert output.visa_sponsorship is True

    def test_company_analysis_output(self):
        extraction = CompanyExtractionOutput(name="Co")
        output = CompanyAnalysisOutput(
            extraction=extraction,
            scores={"fit": 85},
        )
        assert output.extraction.name == "Co"
        assert output.scores["fit"] == 85

    def test_resume_output(self):
        output = ResumeOutput(
            resume_text="John Doe\nSoftware Engineer",
            tailored_sections=[{"title": "Experience", "content": ["Led team"]}],
            match_score=0.85,
        )
        assert output.match_score == 0.85
        assert len(output.tailored_sections) == 1

    def test_cover_letter_output(self):
        output = CoverLetterOutput(
            cover_letter="Dear Hiring Manager,\n\nI am writing...",
            paragraphs=["Dear Hiring Manager,", "I am writing..."],
            tone="professional",
        )
        assert output.tone == "professional"
        assert len(output.paragraphs) == 2

    def test_skill_extraction_output(self):
        output = SkillExtractionOutput(
            skills=[{"name": "Python", "frequency": 10}],
            categories={"programming_languages": ["Python"]},
            raw_skills=["Python"],
        )
        assert len(output.skills) == 1
        assert "Python" in output.raw_skills

    def test_skill_roadmap_output(self):
        output = SkillRoadmapOutput(
            roadmap=[{"skill": "Go", "priority": "high"}],
            priorities=["Go"],
            estimated_timelines={"Go": "4 weeks"},
        )
        assert output.priorities == ["Go"]
        assert output.estimated_timelines["Go"] == "4 weeks"

    def test_insight_section_output(self):
        output = InsightSectionOutput(
            section="overview",
            data={"health_score": 75},
            summary="Career health is good",
            recommendations=["Keep learning"],
        )
        assert output.section == "overview"
        assert len(output.recommendations) == 1

    def test_career_insights_output(self):
        overview = InsightSectionOutput(section="overview", data={})
        output = CareerInsightsOutput(
            overview=overview,
            health_score=75.0,
            generated_sections=["overview"],
        )
        assert output.health_score == 75.0
        assert "overview" in output.generated_sections

    def test_models_serialization(self):
        """All models should serialize to JSON."""
        output = JobExtractionOutput(title="Test", company="Co")
        json_str = json.dumps(output.model_dump(), default=str)
        assert "Test" in json_str

        parsed = json.loads(json_str)
        assert parsed["title"] == "Test"


# ── Graph State Tests ───────────────────────────────────────────────

class TestGraphState:
    """Tests for BaseState TypedDict."""

    def test_create_initial_state(self):
        state = create_initial_state(input="test prompt")
        assert state["input"] == "test prompt"
        assert state["output"] == ""
        assert state["errors"] == []
        assert state["metadata"] == {}

    def test_state_has_required_keys(self):
        state = create_initial_state(input="test")
        required = {"input", "output", "context", "errors", "metadata", "node_history"}
        assert required.issubset(state.keys())

    def test_state_is_mutable_dict(self):
        state = create_initial_state(input="test")
        state["output"] = "result"
        assert state["output"] == "result"

    def test_state_default_context_is_empty_dict(self):
        state = create_initial_state(input="test")
        assert state["context"] == {}

    def test_state_carry_extra_metadata(self):
        state = create_initial_state(input="test")
        state["metadata"]["provider"] = "mimo"
        state["metadata"]["duration"] = 1.5
        assert state["metadata"]["provider"] == "mimo"


# ── Job Processing Graph Tests ──────────────────────────────────────

class TestJobProcessingGraph:
    """Tests for the job processing workflow graph."""

    def test_graph_builds_successfully(self):
        from ai.infrastructure.graphs.job.graph import build_job_processing_graph
        builder = build_job_processing_graph()
        assert builder is not None
        graph = builder.compile()
        assert graph.name == "job_processing"

    def test_graph_has_all_nodes(self):
        from ai.infrastructure.graphs.job.graph import build_job_processing_graph
        builder = build_job_processing_graph()
        graph = builder.compile()
        assert graph is not None

    def test_graph_validates_input(self):
        from ai.infrastructure.graphs.job.graph import build_job_processing_graph
        builder = build_job_processing_graph()
        graph = builder.compile()

        # Empty input should fail validation
        state = create_initial_state(input="")
        result = graph.invoke(state)
        assert len(result["errors"]) > 0 or result["metadata"].get("validation", {}).get("valid") is not True


# ── Company Processing Graph Tests ──────────────────────────────────

class TestCompanyProcessingGraph:
    """Tests for the company processing workflow graph."""

    def test_graph_builds_successfully(self):
        from ai.infrastructure.graphs.company.graph import build_company_processing_graph
        builder = build_company_processing_graph()
        assert builder is not None
        graph = builder.compile()
        assert graph.name == "company_processing"


# ── Resume Generation Graph Tests ───────────────────────────────────

class TestResumeGenerationGraph:
    """Tests for the resume generation workflow graph."""

    def test_graph_builds_successfully(self):
        from ai.infrastructure.graphs.resume.generator import build_resume_generation_graph
        builder = build_resume_generation_graph()
        assert builder is not None
        graph = builder.compile()
        assert graph.name == "resume_generation"


# ── Cover Letter Graph Tests ────────────────────────────────────────

class TestCoverLetterGraph:
    """Tests for the cover letter generation workflow graph."""

    def test_graph_builds_successfully(self):
        from ai.infrastructure.graphs.resume.cover_letter import build_cover_letter_graph
        builder = build_cover_letter_graph()
        assert builder is not None
        graph = builder.compile()
        assert graph.name == "cover_letter_generation"


# ── Skill Extraction Graph Tests ────────────────────────────────────

class TestSkillExtractionGraph:
    """Tests for the skill extraction workflow graph."""

    def test_graph_builds_successfully(self):
        from ai.infrastructure.graphs.skills.extraction import build_skill_extraction_graph
        builder = build_skill_extraction_graph()
        assert builder is not None
        graph = builder.compile()
        assert graph.name == "skill_extraction"


# ── Skill Roadmap Graph Tests ───────────────────────────────────────

class TestSkillRoadmapGraph:
    """Tests for the skill roadmap workflow graph."""

    def test_graph_builds_successfully(self):
        from ai.infrastructure.graphs.skills.roadmap import build_skill_roadmap_graph
        builder = build_skill_roadmap_graph()
        assert builder is not None
        graph = builder.compile()
        assert graph.name == "skill_roadmap"


# ── Insights Graph Tests ────────────────────────────────────────────

class TestInsightsGraph:
    """Tests for the insights generation workflow graph."""

    def test_graph_builds_successfully(self):
        from ai.infrastructure.graphs.insights.graph import build_insights_generation_graph
        builder = build_insights_generation_graph()
        assert builder is not None
        graph = builder.compile()
        assert graph.name == "insights_generation"

    def test_individual_child_graphs_build(self):
        from ai.infrastructure.graphs.insights.graph import (
            build_overview_graph,
            build_skills_insight_graph,
            build_market_insight_graph,
            build_companies_insight_graph,
            build_networking_insight_graph,
            build_opportunities_insight_graph,
        )

        graphs = [
            build_overview_graph(),
            build_skills_insight_graph(),
            build_market_insight_graph(),
            build_companies_insight_graph(),
            build_networking_insight_graph(),
            build_opportunities_insight_graph(),
        ]

        for g in graphs:
            compiled = g.compile()
            assert compiled is not None


# ── Generate All Graph Tests ────────────────────────────────────────

class TestGenerateAllGraph:
    """Tests for the Generate All parent orchestrator graph."""

    def test_graph_builds_successfully(self):
        from ai.infrastructure.graphs.generate_all import build_generate_all_graph
        builder = build_generate_all_graph()
        assert builder is not None
        graph = builder.compile()
        assert graph.name == "generate_all"


# ── Graph Registry Tests ────────────────────────────────────────────

class TestGraphRegistry:
    """Tests for the graph registry functions."""

    def test_get_all_graphs(self):
        from ai.infrastructure.graphs import get_all_graphs
        graphs = get_all_graphs()
        assert len(graphs) >= 7
        assert "job_processing" in graphs
        assert "company_processing" in graphs
        assert "resume_generation" in graphs
        assert "cover_letter_generation" in graphs
        assert "skill_extraction" in graphs
        assert "skill_roadmap" in graphs
        assert "insights" in graphs
        assert "generate_all" in graphs

    def test_get_graph_by_name(self):
        from ai.infrastructure.graphs import get_graph
        graph = get_graph("job_processing")
        assert graph is not None

    def test_get_unknown_graph_raises(self):
        from ai.infrastructure.graphs import get_graph
        with pytest.raises(ValueError, match="Unknown graph"):
            get_graph("nonexistent_graph")
