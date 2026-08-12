"""RoadmapGenerationGraph — LangGraph workflow that generates a job-preparation
roadmap from an Application by reusing the persisted Career Intelligence and
persists it into the Roadmaps context.

    Flow:

    Application
    ↓
    LoadContext → Generate → Persist
    → RoadmapReady | ExecutionFailed

The graph performs exactly one LLM call and reuses the persisted job analysis,
company intelligence and candidate profile (spec 144 §13).
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import START, END, StateGraph

from processing.application.workflows.roadmap_generation.nodes import (
    ExecutionFailedNode,
    GenerateNode,
    LoadContextNode,
    PersistNode,
    RoadmapReadyNode,
)
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.roadmap_generation_state import (
    RoadmapGenerationState,
)

NODE_LOAD_CONTEXT = "load_context"
NODE_GENERATE = "generate"
NODE_PERSIST = "persist"
NODE_ROADMAP_READY = "roadmap_ready"
NODE_EXECUTION_FAILED = "execution_failed"


class RoadmapGenerationGraph:
    def __init__(
        self,
        application_repo: Any,
        job_service: Any,
        analysis_repo: Any,
        company_service: Any,
        intelligence_repo: Any,
        profile_repo: Any,
        roadmap_service: Any,
        llm_service: Any | None = None,
        event_publisher: Any | None = None,
    ):
        self._applications = application_repo
        self._jobs = job_service
        self._analysis = analysis_repo
        self._companies = company_service
        self._intelligence = intelligence_repo
        self._profiles = profile_repo
        self._roadmaps = roadmap_service
        self._llm = llm_service
        self._events = event_publisher
        self._graph = self._build()

    def _build(self):
        graph = StateGraph(RoadmapGenerationState)

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
        graph.add_node(NODE_PERSIST, PersistNode(self._roadmaps, self._jobs, self._events))
        graph.add_node(NODE_ROADMAP_READY, RoadmapReadyNode(self._events))
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
            {NODE_ROADMAP_READY: NODE_ROADMAP_READY, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )

        graph.add_edge(NODE_ROADMAP_READY, END)
        graph.add_edge(NODE_EXECUTION_FAILED, END)

        return graph.compile()

    @staticmethod
    def _after_load(state: RoadmapGenerationState) -> str:
        return NODE_GENERATE if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_generate(state: RoadmapGenerationState) -> str:
        return NODE_PERSIST if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_persist(state: RoadmapGenerationState) -> str:
        return NODE_ROADMAP_READY if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    def invoke(self, state: RoadmapGenerationState) -> RoadmapGenerationState:
        result = self._graph.invoke(state)
        if isinstance(result, dict):
            return RoadmapGenerationState(**result)
        return result