"""MergeNode — folds every extracted source into the canonical candidate profile
and persists a new CandidateProfileVersion.

Delegates to CandidateExtractService.merge_and_persist — the single persistence
path of the Candidates context (core + all children + version snapshot +
processed source rows). The merge is deterministic and idempotent.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.candidate_processing_state import CandidateProcessingState

NODE_ID = "merge"


class MergeNode:
    def __init__(self, extract_service: Any, event_publisher: Any | None = None):
        self._service = extract_service
        self._events = event_publisher

    def __call__(self, state: CandidateProcessingState) -> CandidateProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        if not state.extracted_sources:
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        try:
            result = self._service.merge_and_persist(state.extracted_sources)
        except Exception as e:  # noqa: BLE001 — persistence errors vary
            state.errors.append(f"[{NODE_ID}] Failed to merge candidate profile: {e}")
            state.status = ExecutionStatus.FAILED
            progress_ops.fail_step(self._events, state, NODE_ID, str(e))
            return state

        state.merge_result = result
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
