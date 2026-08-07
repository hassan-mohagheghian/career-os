"""ExtractNode — runs one candidate.extract LLM call per pending source.

Per the approved Phase-101 decision, an extraction failure fails the whole run
(rather than continuing with the remaining sources). Successful extractions are
accumulated into the state so the merge node persists them in a single
operation. Skips (already processed / empty text) are ignored.
"""

from __future__ import annotations

from typing import Any

from candidates.application.adapters.base import SourceContent
from candidates.application.services.candidate_extract_service import CandidateExtractionError
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.candidate_processing_state import CandidateProcessingState

NODE_ID = "extract"


class ExtractNode:
    def __init__(self, extract_service: Any, event_publisher: Any | None = None):
        self._service = extract_service
        self._events = event_publisher

    def __call__(self, state: CandidateProcessingState) -> CandidateProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)

        extracted: list[dict[str, Any]] = []
        total = len(state.pending_sources)
        for i, source in enumerate(state.pending_sources):
            content = SourceContent(
                source_type=source.get("source_type", ""),
                raw_text=source.get("raw_text", ""),
                version=int(source.get("version") or 1),
            )
            try:
                result = self._service.extract(content)
            except CandidateExtractionError as e:
                state.errors.append(f"[{NODE_ID}] {e}")
                state.status = ExecutionStatus.FAILED
                progress_ops.fail_step(self._events, state, NODE_ID, str(e))
                return state
            if result.get("status") == "extracted":
                extracted.append(result)
            if total > 0:
                progress_ops.update_step(
                    self._events, state, NODE_ID, round(((i + 1) / total) * 100, 1)
                )

        state.extracted_sources = extracted
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
