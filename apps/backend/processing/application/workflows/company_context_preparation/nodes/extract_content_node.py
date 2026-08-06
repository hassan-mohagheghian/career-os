"""ExtractContentNode — converts fetched company content into clean text
through the ContentExtractor abstraction.

Emits workflow.step.started/completed events and updates the WorkflowProgress
tree for the extract_content step.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.workflow.company_processing_state import CompanyProcessingState
from processing.domain.workflow.extracted_content import ExtractedContent

NODE_ID = "extract_content"


class ExtractContentNode:
    def __init__(self, extractor: Any, event_publisher: Any | None = None):
        self._extractor = extractor
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)

        extracted: list[ExtractedContent] = []
        total = len(state.fetched_contents)
        for i, fetched in enumerate(state.fetched_contents):
            if not fetched.success:
                continue
            try:
                result = self._extractor.extract(fetched)
            except Exception as e:
                state.errors.append(f"[{NODE_ID}] Extraction failed: {fetched.url}: {e}")
                continue
            extracted.append(result)
            if total > 0:
                progress_ops.update_step(
                    self._events,
                    state,
                    NODE_ID,
                    round(((i + 1) / total) * 100, 1),
                )

        state.extracted_contents = extracted
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
