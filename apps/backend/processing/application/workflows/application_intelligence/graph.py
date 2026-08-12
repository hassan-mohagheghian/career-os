"""ApplicationIntelligenceGraph — LangGraph workflow that generates one
application artifact (tailored resume / cover letter) from existing Career
Intelligence and persists it.

    Flow:

    Application
    ↓
    LoadContext → Generate → Persist
    → ApplicationReady | ExecutionFailed

The graph is parametrized by the intent carried in the state
(ExecutionType.APPLICATION_RESUME / APPLICATION_COVER_LETTER). It performs
exactly one LLM call and reuses the persisted job analysis, company
intelligence and candidate profile.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import START, END, StateGraph

from processing.application.workflows.application_intelligence.nodes import (
    ApplicationReadyNode,
    ExecutionFailedNode,
    GenerateNode,
    LoadContextNode,
    PersistNode,
)
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.application_intelligence_state import (
    ApplicationIntelligenceState,
)

NODE_LOAD_CONTEXT = "load_context"
NODE_GENERATE = "generate"
NODE_PERSIST = "persist"
NODE_APPLICATION_READY = "application_ready"
NODE_EXECUTION_FAILED = "execution_failed"


class ApplicationIntelligenceGraph:
    def __init__(
        self,
        application_repo: Any,
        job_service: Any,
        analysis_repo: Any,
        company_service: Any,
        intelligence_repo: Any,
        profile_repo: Any,
        document_repo: Any,
        llm_service: Any | None = None,
        event_publisher: Any | None = None,
    ):
        self._applications = application_repo
        self._jobs = job_service
        self._analysis = analysis_repo
        self._companies = company_service
        self._intelligence = intelligence_repo
        self._profiles = profile_repo
        self._documents = document_repo
        self._llm = llm_service
        self._events = event_publisher
        self._graph = self._build()

    def _build(self):
        graph = StateGraph(ApplicationIntelligenceState)

        graph.add_node(
            NODE_LOAD_CONTEXT,
            LoadContextNode(
                self._applications,
                self._jobs,
                self._analysis,
                self._companies,
                self._intelligence,
                self._profiles,
                self._events,
            ),
        )
        graph.add_node(NODE_GENERATE, GenerateNode(self._llm, self._events))
        graph.add_node(NODE_PERSIST, PersistNode(self._documents, self._events))
        graph.add_node(NODE_APPLICATION_READY, ApplicationReadyNode(self._events))
        graph.add_node(NODE_EXECUTION_FAILED, ExecutionFailedNode(self._events))

        graph.add_edge(START, NODE_LOAD_CONTEXT)

        graph.add_conditional_edges(
            NODE_LOAD_CONTEXT,
            self._after_load,
            {NODE_GENERATE: NODE_GENERATE, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_conditional_edges(
            NODE_GENERATE,
            self._after_generate,
            {NODE_PERSIST: NODE_PERSIST, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_conditional_edges(
            NODE_PERSIST,
            self._after_persist,
            {NODE_APPLICATION_READY: NODE_APPLICATION_READY, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )

        graph.add_edge(NODE_APPLICATION_READY, END)
        graph.add_edge(NODE_EXECUTION_FAILED, END)

        return graph.compile()

    @staticmethod
    def _after_load(state: ApplicationIntelligenceState) -> str:
        return NODE_GENERATE if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_generate(state: ApplicationIntelligenceState) -> str:
        return NODE_PERSIST if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_persist(state: ApplicationIntelligenceState) -> str:
        return NODE_APPLICATION_READY if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    def invoke(self, state: ApplicationIntelligenceState) -> ApplicationIntelligenceState:
        result = self._graph.invoke(state)
        if isinstance(result, dict):
            return ApplicationIntelligenceState(**result)
        return result
