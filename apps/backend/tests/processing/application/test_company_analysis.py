"""Tests for the Company Analysis workflow.

Covers:
- Combined LLM payload validation against CompanyCombinedAnalysisOutput
- Deterministic scoring (fit/success/overall + grades)
- Workflow nodes (LoadContext, PrepareCompany, AnalyzeCompany, ScoreCompany,
  RecommendCompany, SummarizeCompany, PersistCompany)
- The CompanyAnalysisGraph end-to-end (success, invalid LLM payload, persist error)
"""

import json

import pytest

from processing.application.services.company_analysis_scoring import (
    build_company_analysis_result,
    calculate_overall_score,
    grade_for_overall,
)
from processing.application.services.company_analysis_validation import (
    CompanyCombinedAnalysisOutput,
)
from processing.application.workflows.company_analysis import CompanyAnalysisGraph
from processing.application.workflows.company_analysis.nodes import (
    AnalysisReadyNode,
    AnalyzeCompanyNode,
    ExecutionFailedNode,
    LoadContextNode,
    PersistCompanyNode,
    PersistCompanySkillsNode,
    PrepareCompanyNode,
    RecommendCompanyNode,
    ScoreCompanyNode,
    SummarizeCompanyNode,
)
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_data import CompanyData
from processing.domain.workflow.company_processing_state import CompanyProcessingState


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #


def _company_dict(**overrides) -> dict:
    data = {
        "id": "company-uuid-1",
        "name": "Acme GmbH",
        "raw_content": "Prepared context text for Acme.",
    }
    data.update(overrides)
    return data


class FakeCompanyService:
    def __init__(self, company=None, error=None):
        self._company = company
        self._error = error
        self.persisted = None

    def get_company(self, company_id):
        if self._error is not None:
            raise self._error
        return self._company

    def persist_analysis(self, company_id, extraction, intelligence, recommendation, scores, raw_source):
        if self._error is not None:
            raise self._error
        self.persisted = {
            "company_id": company_id,
            "extraction": extraction,
            "intelligence": intelligence,
            "recommendation": recommendation,
            "scores": scores,
            "raw_source": raw_source,
        }


class FakeRuleRepo:
    def __init__(self, rows=None):
        self._rows = rows or [
            {"key": "python_fit", "priority": 1, "category": "FIT", "value": "Python experience"},
        ]

    def get_enabled_by_scopes(self, scopes):
        return self._rows


class FakeLLMService:
    def __init__(self, payload=None, error=None):
        self._payload = payload
        self._error = error
        self.calls = 0

    def generate_structured(self, prompt, schema=None, timeout=None):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return _LLMResponse(json.dumps(self._payload))


class _LLMResponse:
    def __init__(self, content):
        self.content = content


class FakeSkillRepo:
    def __init__(self):
        self.mentions = []
        self.skills = []

    def resolve_skill(self, data):
        self.skills.append(dict(data))
        return len(self.skills)

    def delete_mentions_for_source(self, source_type, source_id):
        self.mentions = [
            m for m in self.mentions if not (m["source_type"] == source_type and m["source_id"] == source_id)
        ]

    def upsert_mentions(self, skill_id, source_type, source_id, status, evidence):
        self.mentions = [
            m for m in self.mentions if not (m["skill_id"] == skill_id and m["source_type"] == source_type and m["source_id"] == source_id)
        ]
        self.mentions.append({
            "skill_id": skill_id,
            "source_type": source_type,
            "source_id": source_id,
            "status": status,
            "evidence": evidence,
        })


def _valid_payload(**overrides) -> dict:
    data = {
        "extraction": {
            "name": "Acme GmbH",
            "website": "https://acme.example",
            "domain": "Developer Tools",
            "industry": "Software",
            "country": "Germany",
            "city": "Berlin",
            "description": "Builds developer tools for the EU market.",
            "company_size": "50-200",
            "company_type": "PRODUCT_COMPANY",
            "logo_url": "https://acme.example/logo.png",
            "founded_year": "2015",
            "headquarters_full": "Berlin, Germany",
            "countries_of_operation": ["Germany", "Netherlands"],
            "products": ["Acme CLI"],
            "tech_stack": {"backend": ["Python", "Django"]},
            "work_environment": {"remote_policy": "Hybrid"},
            "funding_stage": "Series A",
            "funding_amount": "€10M",
            "skills": [
                {"name": "Python", "category": "backend", "evidence": "Uses Python."},
                {"name": "Kubernetes", "category": "infrastructure"},
                "PostgreSQL",
            ],
        },
        "intelligence": {
            "overview": {"description": "A growing dev-tools company.", "size": "50-200 employees"},
        },
        "recommendation": {
            "priority": "A",
            "observation": "Strong Python shop with good growth.",
            "evidence": "Series A, expanding in Berlin.",
            "impact": "Great for senior backend engineers.",
            "action": "Apply directly.",
            "ideal_role": "Senior Backend Engineer",
            "timing": "Now",
        },
        "scores": {
            "fit": 88,
            "success": 72,
            "overall": 80,
            "fit_grade": "A",
            "fit_explanation": "Strong Python alignment.",
            "fit_positive_factors": ["Python", "Growth"],
            "fit_negative_factors": ["Remote-first only"],
            "success_explanation": "Berlin English-first team.",
            "success_positive_factors": ["Visa sponsorship"],
            "success_negative_factors": ["Competitive market"],
            "overall_grade": "A",
        },
    }
    data.update(overrides)
    return data


class RecordingEventPublisher:
    def __init__(self):
        self.events = []

    def publish(self, event_name, execution_id, job_id, status, **kwargs):
        self.events.append((event_name, execution_id, job_id, status, kwargs))


def _initial_state(company_id="company-uuid-1", execution_id="exec-1") -> CompanyProcessingState:
    return CompanyProcessingState(execution_id=execution_id, company_id=company_id)


def _state_with_company() -> CompanyProcessingState:
    from processing.domain.workflow.company_processing_context import CompanyProcessingContext

    state = _initial_state()
    state.company = CompanyData.from_company_dict(_company_dict())
    state.processing_context = CompanyProcessingContext(
        company_id=state.company_id,
        combined_text="Prepared context text for Acme.",
    )
    return state


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


class TestCompanyCombinedAnalysisOutput:
    def test_valid_payload_passes(self):
        output = CompanyCombinedAnalysisOutput.model_validate(_valid_payload())
        assert output.extraction.name == "Acme GmbH"
        assert output.scores.fit == 88

    def test_missing_scores_rejected(self):
        payload = _valid_payload()
        payload.pop("scores")
        with pytest.raises(Exception):
            CompanyCombinedAnalysisOutput.model_validate(payload)

    def test_missing_extraction_rejected(self):
        payload = _valid_payload()
        payload.pop("extraction")
        with pytest.raises(Exception):
            CompanyCombinedAnalysisOutput.model_validate(payload)

    def test_bad_company_type_coerced_to_unknown(self):
        payload = _valid_payload()
        payload["extraction"]["company_type"] = "SPACESHIP"
        output = CompanyCombinedAnalysisOutput.model_validate(payload)
        assert output.extraction.company_type == "UNKNOWN"

    def test_scores_clamped(self):
        payload = _valid_payload()
        payload["scores"]["fit"] = 150
        payload["scores"]["success"] = -5
        output = CompanyCombinedAnalysisOutput.model_validate(payload)
        assert output.scores.fit == 100
        assert output.scores.success == 0

    def test_skills_coerced_from_dicts_and_strings(self):
        payload = _valid_payload()
        payload["extraction"]["skills"] = [
            {"name": "Python", "category": "backend", "evidence": "Used widely"},
            "PostgreSQL",
            {"name": "   "},
        ]
        output = CompanyCombinedAnalysisOutput.model_validate(payload)
        names = [s.name for s in output.extraction.skills]
        assert names == ["Python", "PostgreSQL"]
        assert output.extraction.skills[0].category == "backend"
        assert output.extraction.skills[0].evidence == "Used widely"

    def test_skills_default_empty(self):
        payload = _valid_payload()
        payload["extraction"].pop("skills", None)
        output = CompanyCombinedAnalysisOutput.model_validate(payload)
        assert output.extraction.skills == []


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #


class TestCompanyScoring:
    def test_overall_is_weighted_average(self):
        assert calculate_overall_score(100, 100) == 100
        assert calculate_overall_score(0, 0) == 0
        assert calculate_overall_score(80, 60) == 70

    def test_grades(self):
        assert grade_for_overall(92) == "A++"
        assert grade_for_overall(85) == "A+"
        assert grade_for_overall(75) == "A"
        assert grade_for_overall(55) == "B"
        assert grade_for_overall(35) == "C"
        assert grade_for_overall(10) == "D"
        assert grade_for_overall(None) == "P"

    def test_build_result_normalizes(self):
        result = build_company_analysis_result(_valid_payload())
        assert result["extraction"]["name"] == "Acme GmbH"
        assert result["scores"]["fit"] == 88
        assert result["scores"]["overall"] == 80
        assert result["scores"]["fit_grade"] == "A+"
        assert result["scores"]["overall_grade"] == "A+"
        assert "company_fit_score" not in result["scores"]
        assert "company_success_score" not in result["scores"]
        assert "company_overall_score" not in result["scores"]

    def test_validated_payload_scores_survive_round_trip(self):
        """Regression: the validated payload (raw_payload) must keep its scores.

        AnalyzeCompanyNode persists CompanyCombinedAnalysisOutput.model_dump(),
        and ScoreCompanyNode builds the result from that. The scores must not be
        lost between validation and scoring.
        """
        validated = CompanyCombinedAnalysisOutput.model_validate(_valid_payload()).model_dump()
        result = build_company_analysis_result(validated)
        assert result["scores"]["fit"] == 88
        assert result["scores"]["success"] == 72
        assert result["scores"]["overall"] == 80
        assert result["scores"]["fit_grade"] == "A+"
        assert result["scores"]["overall_grade"] == "A+"


# --------------------------------------------------------------------------- #
# Prompt builder
# --------------------------------------------------------------------------- #


class TestCompanyAnalysisPrompt:
    def test_prompt_enforces_tight_output_size_limits(self):
        """Regression: the combined prompt must keep the reply short so the
        model output stays under its token ceiling and is never truncated."""
        from processing.application.services.company_analysis_prompt import (
            build_company_analysis_prompt,
        )

        prompt = build_company_analysis_prompt(
            "Prepared context text for Acme.",
            "PRODUCT_COMPANY",
            "python_fit: required",
        )

        assert "at most 50 words" in prompt
        assert "at most 15 words" in prompt
        assert "at most 3 items" in prompt
        assert "~1600 words" in prompt
        assert "Never truncate the output" in prompt

    def test_prompt_forbids_duplicating_extraction_facts(self):
        from processing.application.services.company_analysis_prompt import (
            build_company_analysis_prompt,
        )

        prompt = build_company_analysis_prompt(
            "Prepared context text for Acme.",
            "PRODUCT_COMPANY",
            "",
        )

        assert "Do NOT duplicate extraction facts" in prompt

    def test_prompt_dropped_low_value_intelligence_fields(self):
        """The trimmed template must not enumerate the low-value sub-fields
        whose removal keeps the output inside the model's token budget."""
        from processing.application.services.company_analysis_prompt import (
            build_company_analysis_prompt,
        )

        prompt = build_company_analysis_prompt(
            "Prepared context text for Acme.",
            "PRODUCT_COMPANY",
            "",
        )

        assert "engineering_blog" not in prompt
        assert '"environment"' not in prompt
        assert "salary_info" not in prompt
        assert '"equity"' not in prompt
        assert '"pension"' not in prompt

    def test_prompt_keeps_rendered_intelligence_fields(self):
        """Fields the frontend draws must remain present in the template."""
        from processing.application.services.company_analysis_prompt import (
            build_company_analysis_prompt,
        )

        prompt = build_company_analysis_prompt(
            "Prepared context text for Acme.",
            "PRODUCT_COMPANY",
            "",
        )

        for field in (
            "engineering_org",
            "team_structure",
            "methodology",
            "market_position",
            "growth_trajectory",
            "visa_analysis",
            "technology_analysis",
            "recommendation",
            "scores",
        ):
            assert field in prompt

    def test_prompt_includes_candidate_resume_and_profile(self):
        from processing.application.services.company_analysis_prompt import (
            build_company_analysis_prompt,
        )

        prompt = build_company_analysis_prompt(
            "Acme builds dev tools.",
            "PRODUCT_COMPANY",
            "python_fit: required",
            resume_text="Senior Python engineer resume body",
            profile_documents="CANDIDATE PROFILE (canonical): Backend Lead",
        )

        assert "CANDIDATE RESUME" in prompt
        assert "Senior Python engineer resume body" in prompt
        assert "Backend Lead" in prompt

    def test_prompt_resume_defaults_to_empty_but_renders_sections(self):
        from processing.application.services.company_analysis_prompt import (
            build_company_analysis_prompt,
        )

        prompt = build_company_analysis_prompt("Acme builds dev tools.", "UNKNOWN", "")

        assert "CANDIDATE RESUME" in prompt
        assert "CANDIDATE PROFILE / LINKEDIN" in prompt


# --------------------------------------------------------------------------- #
# Nodes
# --------------------------------------------------------------------------- #


class TestLoadContextNode:
    def test_loads_company_and_sets_combined_text(self):
        node = LoadContextNode(FakeCompanyService(_company_dict()))
        state = node(_initial_state())
        assert state.company is not None
        assert state.processing_context is not None
        assert state.processing_context.combined_text == "Prepared context text for Acme."

    def test_missing_company_fails(self):
        node = LoadContextNode(FakeCompanyService(None))
        state = node(_initial_state())
        assert any("not found" in e for e in state.errors)
        assert state.status == ExecutionStatus.FAILED


class TestPrepareCompanyNode:
    def test_populates_analysis_context(self):
        state = _state_with_company()
        node = PrepareCompanyNode(FakeRuleRepo())
        state = node(state)

        assert state.analysis_context["company_text"]
        assert state.analysis_context["company_type"] == "UNKNOWN"
        assert "python_fit" in state.analysis_context["scoring_rules"]


class FakeSourceRepo:
    def __init__(self, raw_texts: dict[str, str]):
        self._raw = raw_texts

    def get_latest_by_type(self, profile_id, source_type):
        raw = self._raw.get(source_type)
        if raw is None:
            return None
        return {"raw_text": raw}


class FakeProfileRepo:
    def __init__(self, profile=None):
        self._profile = profile

    def get_current_profile(self):
        return self._profile


class TestPrepareCompanyNodeResume:
    def test_loads_resume_when_profile_and_source_exist(self):
        state = _state_with_company()
        node = PrepareCompanyNode(
            FakeRuleRepo(),
            source_repo=FakeSourceRepo({
                "resume": "Senior Python engineer resume body",
                "linkedin": "LinkedIn profile body",
            }),
            candidate_profile_repo=FakeProfileRepo({"id": "profile-1"}),
        )
        state = node(state)

        assert "Senior Python engineer resume body" in state.analysis_context["resume_text"]

    def test_uses_structured_profile_when_available(self):
        state = _state_with_company()
        node = PrepareCompanyNode(
            FakeRuleRepo(),
            source_repo=FakeSourceRepo({"resume": "raw resume", "linkedin": "raw linkedin"}),
            candidate_profile_repo=FakeProfileRepo({"id": "profile-1", "headline": "Backend Lead"}),
        )
        state = node(state)

        assert "Backend Lead" in state.analysis_context["profile_documents"]

    def test_no_candidate_inputs_yields_placeholders(self):
        state = _state_with_company()
        node = PrepareCompanyNode(FakeRuleRepo(), source_repo=None, candidate_profile_repo=None)
        state = node(state)

        assert state.analysis_context["resume_text"] == "(no resume available)"
        assert "(no resume or LinkedIn profile available)" in state.analysis_context["profile_documents"]


class TestAnalyzeCompanyNode:
    def _ready_state(self):
        state = _state_with_company()
        state.analysis_context["company_text"] = "Prepared context text for Acme."
        state.analysis_context["company_type"] = "UNKNOWN"
        state.analysis_context["scoring_rules"] = "python_fit: required"
        return state

    def test_valid_payload_accepted(self):
        node = AnalyzeCompanyNode(FakeLLMService(_valid_payload()))
        state = node(self._ready_state())

        raw = state.analysis_context.get("raw_payload")
        assert raw is not None
        assert raw["extraction"]["name"] == "Acme GmbH"
        assert state.errors == []

    def test_invalid_payload_fails_cleanly(self):
        node = AnalyzeCompanyNode(FakeLLMService({"not": "valid"}))
        state = node(self._ready_state())

        assert state.status == ExecutionStatus.FAILED
        assert any("does not match the required format" in e for e in state.errors)


class TestScoreCompanyNode:
    def test_builds_analysis_result(self):
        state = _state_with_company()
        state.analysis_context["raw_payload"] = _valid_payload()
        node = ScoreCompanyNode()
        state = node(state)

        assert state.analysis_result is not None
        assert state.analysis_result["scores"]["overall"] == 80

    def test_scores_survive_analyze_then_score_chain(self):
        """Regression: AnalyzeCompanyNode (validated dump) → ScoreCompanyNode.

        The numeric scores must survive the validation step; this is the exact
        production path that previously produced null scores.
        """
        state = _state_with_company()
        state.analysis_context["company_text"] = "Prepared context text for Acme."
        state.analysis_context["company_type"] = "UNKNOWN"
        state.analysis_context["scoring_rules"] = "python_fit: required"

        analyzed = AnalyzeCompanyNode(FakeLLMService(_valid_payload()))(state)
        assert analyzed.errors == []

        scored = ScoreCompanyNode()(analyzed)
        assert scored.analysis_result["scores"]["fit"] == 88
        assert scored.analysis_result["scores"]["success"] == 72
        assert scored.analysis_result["scores"]["overall"] == 80
        assert scored.analysis_result["scores"]["fit_grade"] == "A+"
        assert scored.analysis_result["scores"]["overall_grade"] == "A+"


class TestRecommendCompanyNode:
    def test_fills_priority(self):
        state = _state_with_company()
        state.analysis_result = build_company_analysis_result(_valid_payload())
        state.analysis_result["recommendation"] = {}
        node = RecommendCompanyNode()
        state = node(state)

        assert state.analysis_result["recommendation"]["priority"] == "A+"


class TestSummarizeCompanyNode:
    def test_fills_observation(self):
        state = _state_with_company()
        result = build_company_analysis_result(_valid_payload())
        result["recommendation"] = {}
        state.analysis_result = result
        node = SummarizeCompanyNode()
        state = node(state)

        assert state.analysis_result["recommendation"]["observation"]


class TestPersistCompanyNode:
    def test_persists_analysis(self):
        service = FakeCompanyService(_company_dict())
        node = PersistCompanyNode(service)
        state = _state_with_company()
        state.analysis_result = build_company_analysis_result(_valid_payload())

        node(state)

        assert service.persisted is not None
        assert service.persisted["company_id"] == "company-uuid-1"
        assert service.persisted["scores"]["overall"] == 80

    def test_persist_error_marks_failed(self):
        service = FakeCompanyService(_company_dict(), error=RuntimeError("db down"))
        node = PersistCompanyNode(service)
        state = _state_with_company()
        state.analysis_result = build_company_analysis_result(_valid_payload())

        node(state)

        assert state.status == ExecutionStatus.FAILED
        assert any("persist" in e for e in state.errors)


class TestPersistCompanySkillsNode:
    def test_persists_mentions_from_extraction_skills(self):
        repo = FakeSkillRepo()
        node = PersistCompanySkillsNode(repo)
        state = _state_with_company()
        state.analysis_result = build_company_analysis_result(_valid_payload())

        node(state)

        assert state.status != ExecutionStatus.FAILED
        assert len(repo.skills) == 3
        assert {s["name"] for s in repo.skills} == {"Python", "Kubernetes", "PostgreSQL"}
        assert all(s["source_type"] == "ai_generated" for s in repo.skills)
        assert len(repo.mentions) == 3
        assert all(m["source_type"] == "company" and m["source_id"] == "company-uuid-1" for m in repo.mentions)

    def test_reprocessing_replaces_mentions(self):
        repo = FakeSkillRepo()
        node = PersistCompanySkillsNode(repo)
        state = _state_with_company()
        state.analysis_result = build_company_analysis_result(_valid_payload())

        node(state)
        node(state)

        assert len(repo.mentions) == 3
        assert len(repo.skills) == 6

    def test_missing_skills_is_noop(self):
        repo = FakeSkillRepo()
        node = PersistCompanySkillsNode(repo)
        state = _state_with_company()
        state.analysis_result = build_company_analysis_result({
            "extraction": {"name": "Acme GmbH", "skills": []},
            "intelligence": {},
            "recommendation": {},
            "scores": {"fit": 50, "success": 50},
        })

        node(state)

        assert state.status != ExecutionStatus.FAILED
        assert repo.mentions == []

    def test_none_skill_repo_is_noop(self):
        node = PersistCompanySkillsNode(None)
        state = _state_with_company()
        state.analysis_result = build_company_analysis_result(_valid_payload())

        node(state)

        assert state.status != ExecutionStatus.FAILED

    def test_error_marks_failed(self):
        repo = FakeSkillRepo()
        node = PersistCompanySkillsNode(repo)
        state = _state_with_company()
        state.analysis_result = build_company_analysis_result(_valid_payload())
        repo.resolve_skill = lambda data: (_ for _ in ()).throw(RuntimeError("db down"))

        node(state)

        assert state.status == ExecutionStatus.FAILED
        assert any("persist" in e for e in state.errors)


class TestTerminalNodes:
    def test_analysis_ready(self):
        state = AnalysisReadyNode()(_state_with_company())
        assert state.status == ExecutionStatus.COMPLETED

    def test_execution_failed(self):
        state = _state_with_company()
        state.errors.append("boom")
        state = ExecutionFailedNode()(state)
        assert state.status == ExecutionStatus.FAILED


# --------------------------------------------------------------------------- #
# Graph
# --------------------------------------------------------------------------- #


class TestCompanyAnalysisGraph:
    def _graph(self, llm=None):
        return CompanyAnalysisGraph(
            company_service=FakeCompanyService(_company_dict()),
            rule_repo=FakeRuleRepo(),
            skill_repo=FakeSkillRepo(),
            llm_service=llm or FakeLLMService(_valid_payload()),
            event_publisher=RecordingEventPublisher(),
        )

    def test_successful_execution(self):
        graph = self._graph()
        state = graph.invoke(_state_with_company())

        assert state.status == ExecutionStatus.COMPLETED
        assert state.analysis_result is not None
        assert state.persisted is True
        assert state.workflow_progress is not None
        for step_id in ("analyze_company", "score_company", "recommend_company", "summarize_company", "persist_company"):
            step = next(s for s in state.workflow_progress.steps if s.id == step_id)
            assert step.status.value == "completed", step_id

    def test_missing_company_fails(self):
        graph = CompanyAnalysisGraph(
            company_service=FakeCompanyService(None),
            rule_repo=FakeRuleRepo(),
            llm_service=FakeLLMService(_valid_payload()),
            event_publisher=RecordingEventPublisher(),
        )
        state = graph.invoke(_initial_state())
        assert state.status == ExecutionStatus.FAILED
    def test_invalid_llm_payload_fails(self):
        graph = self._graph(llm=FakeLLMService({"bad": "payload"}))
        state = graph.invoke(_state_with_company())
        assert state.status == ExecutionStatus.FAILED
