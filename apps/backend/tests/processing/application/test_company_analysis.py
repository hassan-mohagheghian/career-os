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
