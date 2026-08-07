"""CandidateProcessingGraph — LangGraph workflow that extracts every pending
candidate source (one candidate.extract LLM call each) and merges all results
into the canonical profile.

    Flow:

    CandidateProfile + pending sources
    ↓
    Extract → Merge
    → CandidateReady | ExecutionFailed

This graph runs after CandidateSourcePreparationGraph and reuses its state. Per
the approved decision, a source extraction failure fails the whole run.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import START, END, StateGraph

from processing.application.workflows.candidate_processing.nodes import (
    CandidateReadyNode,
    ExecutionFailedNode,
    ExtractNode,
    MergeNode,
)
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.candidate_processing_state import CandidateProcessingState

NODE_EXTRACT = "extract"
NODE_MERGE = "merge"
NODE_CANDIDATE_READY = "candidate_ready"
NODE_EXECUTION_FAILED = "execution_failed"


class CandidateProcessingGraph:
    def __init__(
        self,
        extract_service: Any,
        event_publisher: Any | None = None,
    ):
        self._extract_service = extract_service
        self._events = event_publisher
        self._graph = self._build()

    def _build(self):
        graph = StateGraph(CandidateProcessingState)

        graph.add_node(NODE_EXTRACT, ExtractNode(self._extract_service, self._events))
        graph.add_node(NODE_MERGE, MergeNode(self._extract_service, self._events))
        graph.add_node(NODE_CANDIDATE_READY, CandidateReadyNode(self._events))
        graph.add_node(NODE_EXECUTION_FAILED, ExecutionFailedNode(self._events))

        graph.add_edge(START, NODE_EXTRACT)

        graph.add_conditional_edges(
            NODE_EXTRACT,
            self._after_extract,
            {NODE_MERGE: NODE_MERGE, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_conditional_edges(
            NODE_MERGE,
            self._after_merge,
            {NODE_CANDIDATE_READY: NODE_CANDIDATE_READY, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_edge(NODE_CANDIDATE_READY, END)
        graph.add_edge(NODE_EXECUTION_FAILED, END)

        return graph.compile()

    @staticmethod
    def _after_extract(state: CandidateProcessingState) -> str:
        return NODE_MERGE if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_merge(state: CandidateProcessingState) -> str:
        return NODE_CANDIDATE_READY if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    def invoke(self, state: CandidateProcessingState) -> CandidateProcessingState:
        result = self._graph.invoke(state)
        if isinstance(result, dict):
            return CandidateProcessingState(**result)
        return result
