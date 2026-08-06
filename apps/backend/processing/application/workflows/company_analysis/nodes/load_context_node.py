"""LoadContextNode — rebuilds the analysis context for a company.

The analysis graph runs after context preparation. It loads the company from
the Companies bounded context (the prepared context was persisted to the
company's raw_content by the prep phase) and rebuilds a CompanyProcessingContext
as the LLM input.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_data import CompanyData
from processing.domain.workflow.company_processing_context import CompanyProcessingContext
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "load_context"


class LoadContextNode:
    def __init__(self, company_service: Any, event_publisher: Any | None = None):
        self._company_service = company_service
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        try:
            company = self._company_service.get_company(state.company_id)
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to load company {state.company_id}: {e}")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        if company is None:
            state.errors.append(f"[{NODE_ID}] Company {state.company_id} not found")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        state.company = CompanyData.from_company_dict(company)
        company_text = company.get("raw_content") or company.get("description") or ""
        if not company_text:
            state.errors.append(f"[{NODE_ID}] Company {state.company_id} has no prepared content")
            state.status = ExecutionStatus.FAILED
        state.processing_context = CompanyProcessingContext(
            company_id=state.company_id,
            company=state.company,
            combined_text=company_text,
        )
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
