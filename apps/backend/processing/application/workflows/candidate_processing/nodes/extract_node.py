"""ExtractNode — runs one candidate.extract LLM call per pending source.

Per the approved Phase-101 decision, an extraction failure fails the whole run
(rather than continuing with the remaining sources). Successful extractions are
accumulated into the state so the merge node persists them in a single
operation. Skips (already processed / empty text) are ignored.
"""

from __future__ import annotations

import time
from typing import Any

from candidates.application.adapters.base import SourceContent
from candidates.application.services.candidate_extract_service import CandidateExtractionError
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.candidate_processing_state import CandidateProcessingState
from shared.infrastructure.process.logging_config import get_logger

log = get_logger("processing.extract_node")

NODE_ID = "extract"


class ExtractNode:
    def __init__(self, extract_service: Any, event_publisher: Any | None = None):
        self._service = extract_service
        self._events = event_publisher

    def __call__(self, state: CandidateProcessingState) -> CandidateProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)

        extracted: list[dict[str, Any]] = []
        total = len(state.pending_sources)
        log.info("extract_node.start", total_sources=total, profile_id=state.profile_id)
        for i, source in enumerate(state.pending_sources):
            source_type = source.get("source_type", "")
            version = int(source.get("version") or 1)
            content = SourceContent(
                source_type=source_type,
                raw_text=source.get("raw_text", ""),
                version=version,
            )
            start = time.time()
            try:
                result = self._service.extract(content)
                duration = round(time.time() - start, 2)
                log.info(
                    "extract_node.source_done",
                    source_type=source_type,
                    version=version,
                    status=result.get("status"),
                    duration=duration,
                )
            except CandidateExtractionError as e:
                duration = round(time.time() - start, 2)
                log.error(
                    "extract_node.source_failed",
                    source_type=source_type,
                    version=version,
                    error=str(e),
                    duration=duration,
                )
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
        log.info("extract_node.complete", extracted_count=len(extracted))
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
