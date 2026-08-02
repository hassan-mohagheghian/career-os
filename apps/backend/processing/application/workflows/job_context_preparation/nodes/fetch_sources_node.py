"""FetchSourcesNode — fetches all external sources through the ContentFetcher
abstraction.

Supports multiple URLs and handles individual failures: one failed source
must not fail the entire workflow. Emits per-source child progress events and
updates the WorkflowProgress tree.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.job_processing_state import JobProcessingState
from processing.domain.workflow.workflow_step import WorkflowStepStatus

NODE_ID = "fetch_sources"


class FetchSourcesNode:
    def __init__(self, fetcher: Any, event_publisher: Any | None = None):
        self._fetcher = fetcher
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)

        fetchable = [s for s in state.sources if s.is_fetchable]
        fetched: list[FetchedContent] = []

        children = [
            {
                "id": f"source_{i}",
                "node_id": NODE_ID,
                "title": self._display_title(source),
                "status": WorkflowStepStatus.PENDING.value,
                "displayable": True,
            }
            for i, source in enumerate(fetchable)
        ]
        progress_ops.replace_children(self._events, state, NODE_ID, children)

        total = len(fetchable)
        for i, source in enumerate(fetchable):
            child_id = f"source_{i}"
            progress_ops.update_child(
                self._events, state, NODE_ID, child_id, WorkflowStepStatus.PROCESSING
            )
            try:
                result = self._fetcher.fetch(source)
            except Exception as e:
                result = FetchedContent(
                    source=source,
                    url=source.url or "",
                    success=False,
                    error=f"{type(e).__name__}: {e}",
                )
            if result.success:
                progress_ops.update_child(
                    self._events,
                    state,
                    NODE_ID,
                    child_id,
                    WorkflowStepStatus.COMPLETED,
                    progress_value=100.0,
                )
            else:
                progress_ops.update_child(
                    self._events,
                    state,
                    NODE_ID,
                    child_id,
                    WorkflowStepStatus.FAILED,
                    progress_value=100.0,
                    error=result.error or "Fetch failed",
                )
            fetched.append(result)
            if total > 0:
                progress_ops.update_step(
                    self._events,
                    state,
                    NODE_ID,
                    round(((i + 1) / total) * 100, 1),
                )

        state.fetched_contents = fetched
        state.errors.extend(
            f"Fetch failed: {f.url}: {f.error}"
            for f in fetched if not f.success and f.error
        )
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    @staticmethod
    def _display_title(source) -> str:
        if getattr(source, "title", None):
            return source.title
        url = source.url or ""
        return url.split("://")[-1][:60] or "Untitled Source"
