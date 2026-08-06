"""PersistCompanyNode — writes the company analysis result to the database.

Writes:
  - the queryable extraction fields onto the companies row
  - the company_intelligence row (intelligence sections + recommendation + scores)
  - sets the company status to `processed`
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "persist_company"


class PersistCompanyNode:
    def __init__(self, company_service: Any, event_publisher: Any | None = None):
        self._company_service = company_service
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        result = state.analysis_result or {}
        if not result:
            state.errors.append(f"[{NODE_ID}] No analysis result to persist for {state.company_id}")
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        raw_source = state.processing_context.combined_text if state.processing_context else ""

        try:
            self._company_service.persist_analysis(
                state.company_id,
                extraction=result.get("extraction") or {},
                intelligence=result.get("intelligence") or {},
                recommendation=result.get("recommendation") or {},
                scores=result.get("scores") or {},
                raw_source=raw_source,
            )
            state.persisted = True
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to persist analysis: {e}")
            state.status = ExecutionStatus.FAILED
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
