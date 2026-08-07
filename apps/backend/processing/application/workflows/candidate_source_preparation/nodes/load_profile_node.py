"""LoadProfileNode — loads the current candidate profile through the Candidates
bounded context.

Uses ICandidateProfileRepository (get_or_create_current) — it does not access
the database directly. Emits workflow.step.started/completed events and updates
the WorkflowProgress tree for the load_profile step.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.candidate_processing_state import CandidateProcessingState

NODE_ID = "load_profile"


class LoadProfileNode:
    def __init__(self, profile_repo: Any, event_publisher: Any | None = None):
        self._profile_repo = profile_repo
        self._events = event_publisher

    def __call__(self, state: CandidateProcessingState) -> CandidateProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        try:
            profile = self._profile_repo.get_or_create_current()
        except Exception as e:  # noqa: BLE001 — repo errors vary
            state.errors.append(f"[{NODE_ID}] Failed to load candidate profile: {e}")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        if not profile or not profile.get("id"):
            state.errors.append("[{NODE_ID}] Candidate profile not found")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        state.profile = profile
        state.profile_id = profile.get("id") or state.profile_id
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
