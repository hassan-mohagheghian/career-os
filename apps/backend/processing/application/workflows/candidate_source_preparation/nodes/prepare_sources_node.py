"""PrepareSourcesNode — collects the raw contents of every available candidate
source through the source adapters (resume, linkedin, ...).

No LLM is involved in this phase. The source repo is consulted so already-known
source versions are not fetched again; the extract phase (CandidateExtractService)
performs the authoritative already-processed check and skip. Emits workflow
progress events and updates the WorkflowProgress tree for the prepare_sources
step.
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
        known = self._known_source_versions(state.profile_id)

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
            if (content.source_type, content.version) in known:
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

    def _known_source_versions(self, profile_id: str) -> set[tuple[str, int]]:
        if not profile_id:
            return set()
        try:
            rows = self._source_repo.list_for_profile(profile_id)
        except Exception:  # noqa: BLE001 — best-effort lookup
            return set()
        # Only processed sources count as "known". Pending sources (e.g. just
        # uploaded via POST /candidates/sources) must still be fetched/extracted.
        return {
            (str(r.get("source_type")), int(r.get("version") or 0))
            for r in rows
            if r.get("status") == "processed"
        }
