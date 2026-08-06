"""CompanyAnalysisGraph — LangGraph workflow that runs the single combined LLM
analysis for a company and persists the result.

    Flow:

    Company
    ↓
    LoadContext → PrepareCompany → AnalyzeCompany → ScoreCompany
    → RecommendCompany → SummarizeCompany → PersistCompany
    → PersistCompanySkills → AnalysisReady | ExecutionFailed

This graph runs after CompanyContextPreparationGraph and reuses its state (and
the persisted prepared context). It performs exactly one LLM call
(company.analyze_company).
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import START, END, StateGraph

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
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_LOAD_CONTEXT = "load_context"
NODE_PREPARE_COMPANY = "prepare_company"
NODE_ANALYZE_COMPANY = "analyze_company"
NODE_SCORE_COMPANY = "score_company"
NODE_RECOMMEND_COMPANY = "recommend_company"
NODE_SUMMARIZE_COMPANY = "summarize_company"
NODE_PERSIST_COMPANY = "persist_company"
NODE_PERSIST_COMPANY_SKILLS = "persist_company_skills"
NODE_ANALYSIS_READY = "analysis_ready"
NODE_EXECUTION_FAILED = "execution_failed"

OUTCOME_READY = "analysis_ready"
OUTCOME_FAILED = "execution_failed"


class CompanyAnalysisGraph:
    def __init__(
        self,
        company_service: Any,
        rule_repo: Any,
        skill_repo: Any | None = None,
        llm_service: Any | None = None,
        event_publisher: Any | None = None,
    ):
        self._company_service = company_service
        self._rules = rule_repo
        self._skills = skill_repo
        self._llm = llm_service
        self._events = event_publisher
        self._graph = self._build()

    def _build(self):
        graph = StateGraph(CompanyProcessingState)

        graph.add_node(NODE_LOAD_CONTEXT, LoadContextNode(self._company_service, self._events))
        graph.add_node(NODE_PREPARE_COMPANY, PrepareCompanyNode(self._rules, self._events))
        graph.add_node(NODE_ANALYZE_COMPANY, AnalyzeCompanyNode(self._llm, self._events))
        graph.add_node(NODE_SCORE_COMPANY, ScoreCompanyNode(self._events))
        graph.add_node(NODE_RECOMMEND_COMPANY, RecommendCompanyNode(self._events))
        graph.add_node(NODE_SUMMARIZE_COMPANY, SummarizeCompanyNode(self._events))
        graph.add_node(NODE_PERSIST_COMPANY, PersistCompanyNode(self._company_service, self._events))
        graph.add_node(NODE_PERSIST_COMPANY_SKILLS, PersistCompanySkillsNode(self._skills, self._events))
        graph.add_node(NODE_ANALYSIS_READY, AnalysisReadyNode(self._events))
        graph.add_node(NODE_EXECUTION_FAILED, ExecutionFailedNode(self._events))

        graph.add_edge(START, NODE_LOAD_CONTEXT)

        graph.add_conditional_edges(
            NODE_LOAD_CONTEXT,
            self._after_load,
            {NODE_PREPARE_COMPANY: NODE_PREPARE_COMPANY, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_edge(NODE_PREPARE_COMPANY, NODE_ANALYZE_COMPANY)

        graph.add_conditional_edges(
            NODE_ANALYZE_COMPANY,
            self._after_analyze,
            {NODE_SCORE_COMPANY: NODE_SCORE_COMPANY, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )

        graph.add_edge(NODE_SCORE_COMPANY, NODE_RECOMMEND_COMPANY)
        graph.add_edge(NODE_RECOMMEND_COMPANY, NODE_SUMMARIZE_COMPANY)
        graph.add_edge(NODE_SUMMARIZE_COMPANY, NODE_PERSIST_COMPANY)

        graph.add_conditional_edges(
            NODE_PERSIST_COMPANY,
            self._after_persist,
            {NODE_PERSIST_COMPANY_SKILLS: NODE_PERSIST_COMPANY_SKILLS, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_edge(NODE_PERSIST_COMPANY_SKILLS, NODE_ANALYSIS_READY)

        graph.add_edge(NODE_ANALYSIS_READY, END)
        graph.add_edge(NODE_EXECUTION_FAILED, END)

        return graph.compile()

    @staticmethod
    def _after_load(state: CompanyProcessingState) -> str:
        return NODE_PREPARE_COMPANY if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_analyze(state: CompanyProcessingState) -> str:
        return NODE_SCORE_COMPANY if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_persist(state: CompanyProcessingState) -> str:
        return NODE_PERSIST_COMPANY_SKILLS if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    def invoke(self, state: CompanyProcessingState) -> CompanyProcessingState:
        result = self._graph.invoke(state)
        if isinstance(result, dict):
            return CompanyProcessingState(**result)
        return result
