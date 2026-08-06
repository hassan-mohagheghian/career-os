"""LoadCompanyNode — loads Company information through the Companies bounded
context.

Uses CompanyService (CompanyRepository) — it does not access the database
directly. Emits workflow.step.started/completed events and updates the
WorkflowProgress tree for the load_company step.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_data import CompanyData
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "load_company"


class LoadCompanyNode:
    def __init__(self, company_service: Any, event_publisher: Any | None = None):
        self._company_service = company_service
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        try:
            company = self._company_service.get_company(state.company_id)
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to load company {state.company_id}: {e}")
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        if company is None:
            state.errors.append(f"[{NODE_ID}] Company {state.company_id} not found")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        try:
            state.company = CompanyData.from_company_dict(company)
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to parse company data: {e}")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        state.company_id = company.get("id") or state.company_id
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
