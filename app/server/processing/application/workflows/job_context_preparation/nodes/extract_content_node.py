"""ExtractContentNode — converts fetched data into clean text through the
ContentExtractor abstraction.

Emits the processing.extracting_content event.
"""

from __future__ import annotations

from typing import Any

from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.job_processing_state import JobProcessingState
from shared.infrastructure.events.processing_events import CONTEXT_EXTRACTING_CONTENT


class ExtractContentNode:
    def __init__(self, extractor: Any, event_publisher: Any | None = None):
        self._extractor = extractor
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        self._emit(state)

        extracted: list[ExtractedContent] = []
        for fetched in state.fetched_contents:
            if not fetched.success:
                continue
            try:
                result = self._extractor.extract(fetched)
            except Exception as e:
                state.errors.append(f"Extraction failed: {fetched.url}: {e}")
                continue
            extracted.append(result)

        state.extracted_contents = extracted
        return state

    def _emit(self, state: JobProcessingState) -> None:
        if self._events is None:
            return
        self._events.publish(
            CONTEXT_EXTRACTING_CONTENT,
            state.execution_id,
            state.job_id,
            "running",
            current_step="extracting_content",
            message="Extracting clean text from fetched content",
        )
