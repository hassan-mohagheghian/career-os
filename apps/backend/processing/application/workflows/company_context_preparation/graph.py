"""CompanyContextPreparationGraph — LangGraph workflow that prepares a complete
and validated context for a Company before any LLM-based analysis starts.

Flow:

    Company
    ↓
    LoadCompany → CollectSources → FetchSources → ExtractContent
    → BuildContext → ValidateContext
    → (valid) ContextReady | (invalid) ExecutionFailed

This phase must NOT include any LLM calls.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import START, END, StateGraph

from processing.application.services.company_context_builder import CompanyContextBuilderService
from processing.application.services.company_context_validator import CompanyContextValidatorService
from processing.application.workflows.company_context_preparation.nodes import (
    BuildContextNode,
    CollectSourcesNode,
    ContextReadyNode,
    ExecutionFailedNode,
    ExtractContentNode,
    FetchSourcesNode,
    LoadCompanyNode,
    PersistContextNode,
    ValidateContextNode,
)
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_LOAD_COMPANY = "load_company"
NODE_COLLECT_SOURCES = "collect_sources"
NODE_FETCH_SOURCES = "fetch_sources"
NODE_EXTRACT_CONTENT = "extract_content"
NODE_BUILD_CONTEXT = "build_context"
NODE_VALIDATE_CONTEXT = "validate_context"
NODE_PERSIST_CONTEXT = "persist_context"
NODE_CONTEXT_READY = "context_ready"
NODE_EXECUTION_FAILED = "execution_failed"

OUTCOME_READY = "context_ready"
OUTCOME_FAILED = "execution_failed"


class CompanyContextPreparationGraph:
    def __init__(
        self,
        company_service: Any,
        fetcher: Any,
        extractor: Any,
        builder: Any | None = None,
        validator: Any | None = None,
        event_publisher: Any | None = None,
    ):
        self._company_service = company_service
        self._fetcher = fetcher
        self._extractor = extractor
        self._builder = builder or CompanyContextBuilderService()
        self._validator = validator or CompanyContextValidatorService()
        self._event_publisher = event_publisher
        self._graph = self._build()

    def _build(self):
        graph = StateGraph(CompanyProcessingState)

        graph.add_node(NODE_LOAD_COMPANY, LoadCompanyNode(self._company_service, self._event_publisher))
        graph.add_node(NODE_COLLECT_SOURCES, CollectSourcesNode(self._event_publisher))
        graph.add_node(NODE_FETCH_SOURCES, FetchSourcesNode(self._fetcher, self._event_publisher))
        graph.add_node(NODE_EXTRACT_CONTENT, ExtractContentNode(self._extractor, self._event_publisher))
        graph.add_node(NODE_BUILD_CONTEXT, BuildContextNode(self._builder, self._event_publisher))
        graph.add_node(NODE_VALIDATE_CONTEXT, ValidateContextNode(self._validator, self._event_publisher))
        graph.add_node(NODE_PERSIST_CONTEXT, PersistContextNode(self._company_service, self._event_publisher))
        graph.add_node(NODE_CONTEXT_READY, ContextReadyNode(self._event_publisher))
        graph.add_node(NODE_EXECUTION_FAILED, ExecutionFailedNode(self._event_publisher))

        graph.add_edge(START, NODE_LOAD_COMPANY)

        graph.add_conditional_edges(
            NODE_LOAD_COMPANY,
            self._after_load,
            {NODE_COLLECT_SOURCES: NODE_COLLECT_SOURCES, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_edge(NODE_COLLECT_SOURCES, NODE_FETCH_SOURCES)
        graph.add_edge(NODE_FETCH_SOURCES, NODE_EXTRACT_CONTENT)
        graph.add_edge(NODE_EXTRACT_CONTENT, NODE_BUILD_CONTEXT)
        graph.add_edge(NODE_BUILD_CONTEXT, NODE_VALIDATE_CONTEXT)

        graph.add_conditional_edges(
            NODE_VALIDATE_CONTEXT,
            self._after_validate,
            {NODE_PERSIST_CONTEXT: NODE_PERSIST_CONTEXT, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )

        graph.add_conditional_edges(
            NODE_PERSIST_CONTEXT,
            self._after_persist,
            {NODE_CONTEXT_READY: NODE_CONTEXT_READY, NODE_EXECUTION_FAILED: NODE_EXECUTION_FAILED},
        )
        graph.add_edge(NODE_CONTEXT_READY, END)
        graph.add_edge(NODE_EXECUTION_FAILED, END)

        return graph.compile()

    @staticmethod
    def _after_load(state: CompanyProcessingState) -> str:
        return NODE_COLLECT_SOURCES if state.company is not None else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_validate(state: CompanyProcessingState) -> str:
        result = state.validation_result
        return NODE_PERSIST_CONTEXT if result is not None and result.valid else NODE_EXECUTION_FAILED

    @staticmethod
    def _after_persist(state: CompanyProcessingState) -> str:
        return NODE_CONTEXT_READY if state.status != ExecutionStatus.FAILED else NODE_EXECUTION_FAILED

    def invoke(self, state: CompanyProcessingState) -> CompanyProcessingState:
        result = self._graph.invoke(state)
        if isinstance(result, dict):
            return CompanyProcessingState(**result)
        return result
