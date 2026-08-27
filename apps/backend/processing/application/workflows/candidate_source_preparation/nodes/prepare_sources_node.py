"""PrepareSourcesNode — collects the raw contents of every available candidate
source through the source adapters (resume, linkedin, ...).

No LLM is involved in this phase. The latest version of each source type is
always fetched so the user can re-process their profile without restriction.
The extract phase (CandidateExtractService) persists the results and marks
sources as processed. Emits workflow progress events and updates the
WorkflowProgress tree for the prepare_sources step.
"""

from __future__ import annotations

from typing import Any

from candidates.application.adapters import build_adapter
from processing.application.workflows import progress_ops
from processing.domain.workflow.candidate_processing_state import CandidateProcessingState

NODE_ID = "prepare_sources"

SOURCE_TYPES = ("resume", "linkedin", "github", "portfolio")


class PrepareSourcesNode:
    def __init__(
        self,
        source_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._source_repo = source_repo
        self._events = event_publisher

    def __call__(self, state: CandidateProcessingState) -> CandidateProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        pending: list[dict[str, Any]] = []

        for source_type in SOURCE_TYPES:
            adapter = build_adapter(source_type, self._source_repo, state.profile_id)
            if adapter is None:
                continue
            try:
                content = adapter.fetch()
            except Exception as e:  # noqa: BLE001 — adapter errors vary
                state.errors.append(f"[{NODE_ID}] Fetch failed for {source_type}: {e}")
                continue
            if content is None:
                continue
            pending.append(
                {
                    "source_type": content.source_type,
                    "version": content.version,
                    "raw_text": content.raw_text or "",
                }
            )

        state.pending_sources = pending
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
