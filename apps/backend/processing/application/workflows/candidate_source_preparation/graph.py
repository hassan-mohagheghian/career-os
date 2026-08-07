"""CandidateSourcePreparationGraph — LangGraph workflow that loads the current
candidate profile and collects every available source document's raw content
before any LLM-based extraction starts.

Flow:

    CandidateProfile
    ↓
    LoadProfile → PrepareSources
    → (ready) SourcesReady | (failed) ExecutionFailed

This phase must NOT include any LLM calls.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import START, END, StateGraph

from processing.application.workflows.candidate_source_preparation.nodes import (
    ExecutionFailedNode,
    LoadProfileNode,
    PrepareSourcesNode,
    SourcesReadyNode,
)
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.candidate_processing_state import CandidateProcessingState

NODE_LOAD_PROFILE = "load_profile"
NODE_PREPARE_SOURCES = "prepare_sources"
NODE_SOURCES_READY = "sources_ready"
NODE_EXECUTION_FAILED = "execution_failed"


class CandidateSourcePreparationGraph:
    def __init__(
        self,
        profile_repo: Any,
        source_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._profile_repo = profile_repo
        self._source_repo = source_repo
        self._events = event_publisher
        self._graph = self._build()

    def _build(self):
        graph = StateGraph(CandidateProcessingState)

        graph.add_node(NODE_LOAD_PROFILE, LoadProfileNode(self._profile_repo, self._events))
        graph.add_node(
            NODE_PREPARE_SOURCES,
            PrepareSourcesNode(self._source_repo, self._events),
        )
        graph.add_node(NODE_SOURCES_READY, SourcesReadyNode(self._events))
        graph.add_node(NODE_EXECUTION_FAILED, ExecutionFailedNode(self._events))

        graph.add_edge(START, NODE_LOAD_PROFILE)

        graph.add_conditional_edges(
            NODE_LOAD_PROFILE,
            self._after_load,
            {NODE_PREPARE_SOURCES: NODE_PREPARE_SOURCES, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_conditional_edges(
            NODE_PREPARE_SOURCES,
            self._after_prepare,
            {NODE_SOURCES_READY: NODE_SOURCES_READY, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_edge(NODE_SOURCES_READY, END)
        graph.add_edge(NODE_EXECUTION_FAILED, END)

        return graph.compile()

    @staticmethod
    def _after_load(state: CandidateProcessingState) -> str:
        return NODE_PREPARE_SOURCES if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_prepare(state: CandidateProcessingState) -> str:
        return NODE_SOURCES_READY if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    def invoke(self, state: CandidateProcessingState) -> CandidateProcessingState:
        result = self._graph.invoke(state)
        if isinstance(result, dict):
            return CandidateProcessingState(**result)
        return result
