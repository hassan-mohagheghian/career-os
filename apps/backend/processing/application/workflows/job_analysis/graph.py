"""JobAnalysisGraph — LangGraph workflow that runs the single combined LLM
analysis for a job and persists the result.

    Flow:

        Job
        ↓
        LoadContext → PrepareProfile → Analyze → ExtractSkills → Score
        → Recommend → Summarize → Persist → PersistSkills → LinkCompany
        → AnalysisReady | ExecutionFailed

    This graph runs after JobContextPreparationGraph and reuses its state (and the
    persisted prepared context). It performs exactly one LLM call (job.analyze).
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import START, END, StateGraph

from processing.application.workflows.job_analysis.nodes import (
    AnalysisReadyNode,
    AnalyzeNode,
    ExecutionFailedNode,
    ExtractSkillsNode,
    LinkCompanyNode,
    LoadContextNode,
    PersistNode,
    PersistSkillsNode,
    PrepareProfileNode,
    RecommendNode,
    ScoreNode,
    SummarizeNode,
)
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_LOAD_CONTEXT = "load_context"
NODE_PREPARE_PROFILE = "prepare_profile"
NODE_ANALYZE = "analyze"
NODE_EXTRACT_SKILLS = "extract_skills"
NODE_SCORE = "score"
NODE_RECOMMEND = "recommend"
NODE_SUMMARIZE = "summarize"
NODE_PERSIST = "persist"
NODE_PERSIST_SKILLS = "persist_skills"
NODE_LINK_COMPANY = "link_company"
NODE_ANALYSIS_READY = "analysis_ready"
NODE_EXECUTION_FAILED = "execution_failed"

OUTCOME_READY = "analysis_ready"
OUTCOME_FAILED = "execution_failed"


class JobAnalysisGraph:
    def __init__(
        self,
        job_service: Any,
        skill_repo: Any,
        resume_repo: Any,
        rule_repo: Any,
        job_repo: Any,
        summary_repo: Any,
        analysis_repo: Any,
        matching_service: Any = None,
        llm_service: Any | None = None,
        event_publisher: Any | None = None,
    ):
        self._job_service = job_service
        self._skills = skill_repo
        self._resumes = resume_repo
        self._rules = rule_repo
        self._jobs = job_repo
        self._summaries = summary_repo
        self._analysis = analysis_repo
        self._matching = matching_service
        self._llm = llm_service
        self._events = event_publisher
        self._graph = self._build()

    def _build(self):
        graph = StateGraph(JobProcessingState)

        graph.add_node(NODE_LOAD_CONTEXT, LoadContextNode(self._job_service, self._events))
        graph.add_node(NODE_PREPARE_PROFILE, PrepareProfileNode(self._skills, self._resumes, self._rules, self._events))
        graph.add_node(NODE_ANALYZE, AnalyzeNode(self._llm, self._events))
        graph.add_node(NODE_EXTRACT_SKILLS, ExtractSkillsNode(self._events))
        graph.add_node(NODE_SCORE, ScoreNode(self._events))
        graph.add_node(NODE_RECOMMEND, RecommendNode(self._events))
        graph.add_node(NODE_SUMMARIZE, SummarizeNode(self._events))
        graph.add_node(NODE_PERSIST, PersistNode(self._jobs, self._summaries, self._analysis, self._events))
        graph.add_node(NODE_PERSIST_SKILLS, PersistSkillsNode(self._skills, self._events))
        graph.add_node(NODE_LINK_COMPANY, LinkCompanyNode(self._matching, self._jobs, self._events))
        graph.add_node(NODE_ANALYSIS_READY, AnalysisReadyNode(self._events))
        graph.add_node(NODE_EXECUTION_FAILED, ExecutionFailedNode(self._events))

        graph.add_edge(START, NODE_LOAD_CONTEXT)

        graph.add_conditional_edges(
            NODE_LOAD_CONTEXT,
            self._after_load,
            {NODE_PREPARE_PROFILE: NODE_PREPARE_PROFILE, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_edge(NODE_PREPARE_PROFILE, NODE_ANALYZE)

        graph.add_conditional_edges(
            NODE_ANALYZE,
            self._after_analyze,
            {NODE_EXTRACT_SKILLS: NODE_EXTRACT_SKILLS, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )

        graph.add_edge(NODE_EXTRACT_SKILLS, NODE_SCORE)
        graph.add_edge(NODE_SCORE, NODE_RECOMMEND)
        graph.add_edge(NODE_RECOMMEND, NODE_SUMMARIZE)
        graph.add_edge(NODE_SUMMARIZE, NODE_PERSIST)

        graph.add_conditional_edges(
            NODE_PERSIST,
            self._after_persist,
            {NODE_PERSIST_SKILLS: NODE_PERSIST_SKILLS, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_edge(NODE_PERSIST_SKILLS, NODE_LINK_COMPANY)
        graph.add_edge(NODE_LINK_COMPANY, NODE_ANALYSIS_READY)
        graph.add_edge(NODE_ANALYSIS_READY, END)
        graph.add_edge(NODE_EXECUTION_FAILED, END)

        return graph.compile()

    @staticmethod
    def _after_load(state: JobProcessingState) -> str:
        return NODE_PREPARE_PROFILE if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_analyze(state: JobProcessingState) -> str:
        return NODE_EXTRACT_SKILLS if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_persist(state: JobProcessingState) -> str:
        return NODE_PERSIST_SKILLS if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    def invoke(self, state: JobProcessingState) -> JobProcessingState:
        result = self._graph.invoke(state)
        if isinstance(result, dict):
            return JobProcessingState(**result)
        return result
