"""FetchSourcesNode — fetches all external sources through the ContentFetcher
abstraction.

Supports multiple URLs and handles individual failures: one failed source
must not fail the entire workflow.
"""

from __future__ import annotations

from typing import Any

from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.job_processing_state import JobProcessingState
from shared.infrastructure.events.processing_events import CONTEXT_FETCHING_SOURCES


class FetchSourcesNode:
    def __init__(self, fetcher: Any, event_publisher: Any | None = None):
        self._fetcher = fetcher
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        self._emit(state)

        fetchable = [s for s in state.sources if s.is_fetchable]
        fetched: list[FetchedContent] = []

        for source in fetchable:
            try:
                result = self._fetcher.fetch(source)
            except Exception as e:
                result = FetchedContent(
                    source=source,
                    url=source.url or "",
                    success=False,
                    error=f"{type(e).__name__}: {e}",
                )
            fetched.append(result)

        state.fetched_contents = fetched
        state.errors.extend(
            f"Fetch failed: {f.url}: {f.error}"
            for f in fetched if not f.success and f.error
        )
        return state

    def _emit(self, state: JobProcessingState) -> None:
        if self._events is None:
            return
        self._events.publish(
            CONTEXT_FETCHING_SOURCES,
            state.execution_id,
            state.job_id,
            "running",
            current_step="fetching_sources",
            message="Fetching job sources",
        )
