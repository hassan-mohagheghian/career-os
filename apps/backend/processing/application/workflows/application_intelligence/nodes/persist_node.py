"""PersistNode — writes the generated artifact into the Applications context.

- application_preparation → a new ``application_preparations`` version row.
- application_resume / application_cover_letter → a new
  ``application_documents`` version row (typed by the intent).

Domain events are emitted through the Applications context publisher
(best-effort, in-memory collector).
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from applications.domain.events import (
    ApplicationDocumentGenerated,
    ApplicationPreparationGenerated,
)
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus, ExecutionType
from processing.domain.workflow.application_intelligence_state import (
    ApplicationIntelligenceState,
)

NODE_ID = "persist"


class PersistNode:
    def __init__(
        self,
        preparation_repo: Any,
        document_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._preparations = preparation_repo
        self._documents = document_repo
        self._events = event_publisher

    def __call__(self, state: ApplicationIntelligenceState) -> ApplicationIntelligenceState:
        progress_ops.start_step(self._events, state, NODE_ID)
        result = state.result or {}
        if not result:
            state.errors.append(f"[{NODE_ID}] No generation result to persist")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        try:
            if state.intent == ExecutionType.APPLICATION_PREPARATION:
                state.persisted_id = self._persist_preparation(state, result)
            else:
                state.persisted_id = self._persist_document(state, result)
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to persist generation: {e}")
            state.status = ExecutionStatus.FAILED
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    def _persist_preparation(self, state: ApplicationIntelligenceState, result: dict[str, Any]) -> str:
        now = datetime.now(UTC).isoformat()
        payload = {
            "hard_skills": result.get("hard_skills") or [],
            "soft_skills": result.get("soft_skills") or [],
        }
        stored = self._preparations.create(
            {
                "application_id": state.application_id,
                "version": self._preparations.get_next_version(state.application_id),
                "payload": payload,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._emit(
            ApplicationPreparationGenerated(
                aggregate_id=state.application_id,
                application_id=state.application_id,
                preparation_id=stored["id"],
                version=int(stored.get("version") or 1),
            )
        )
        return stored["id"]

    def _persist_document(self, state: ApplicationIntelligenceState, result: dict[str, Any]) -> str:
        now = datetime.now(UTC).isoformat()
        document_type = (
            "tailored_resume"
            if state.intent == ExecutionType.APPLICATION_RESUME
            else "cover_letter"
        )
        stored = self._documents.create(
            {
                "application_id": state.application_id,
                "document_type": document_type,
                "version": self._documents.get_next_version(state.application_id, document_type),
                "content": result.get("content") or "",
                "created_at": now,
                "updated_at": now,
            }
        )
        self._emit(
            ApplicationDocumentGenerated(
                aggregate_id=state.application_id,
                application_id=state.application_id,
                document_id=stored["id"],
                document_type=document_type,
                version=int(stored.get("version") or 1),
            )
        )
        return stored["id"]

    def _emit(self, event: Any) -> None:
        if self._events is None:
            return
        try:
            self._events.publish(event)
        except Exception:  # noqa: BLE001 — best-effort publishing
            pass
