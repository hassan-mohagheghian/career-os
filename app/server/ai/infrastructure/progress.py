"""ProgressEmitter — emits progress events via WebSocket.

Observer Pattern: Clients subscribe to progress events.
Strategy Pattern: Different emitters for different transport mechanisms.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Optional


class ProgressEvent:
    """Domain event for workflow progress."""

    def __init__(
        self,
        session_id: str,
        stage: str,
        progress: float,
        message: str = "",
        metadata: dict[str, Any] | None = None,
    ):
        self.session_id = session_id
        self.stage = stage
        self.progress = progress
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ProgressEmitter:
    """Emits progress events to connected clients.

    Supports:
    - WebSocket broadcasting
    - Event callbacks
    - Progress persistence
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._broadcast_fn: Optional[Callable] = None

    def set_broadcast_function(self, fn: Callable) -> None:
        """Set the broadcast function for WebSocket events."""
        self._broadcast_fn = fn

    def subscribe(self, session_id: str, callback: Callable) -> None:
        """Subscribe to progress events for a session."""
        if session_id not in self._subscribers:
            self._subscribers[session_id] = []
        self._subscribers[session_id].append(callback)

    def unsubscribe(self, session_id: str, callback: Callable) -> None:
        """Unsubscribe from progress events."""
        if session_id in self._subscribers:
            self._subscribers[session_id] = [
                cb for cb in self._subscribers[session_id] if cb != callback
            ]

    def emit(
        self,
        session_id: str,
        stage: str,
        progress: float,
        message: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a progress event.

        Args:
            session_id: The generation session ID.
            stage: Current stage name.
            progress: Progress value (0.0 to 1.0).
            message: Optional human-readable message.
            metadata: Optional additional metadata.
        """
        event = ProgressEvent(
            session_id=session_id,
            stage=stage,
            progress=progress,
            message=message,
            metadata=metadata,
        )

        # Notify subscribers
        for callback in self._subscribers.get(session_id, []):
            try:
                callback(event)
            except Exception:
                pass

        # Broadcast via WebSocket
        if self._broadcast_fn:
            try:
                self._broadcast_fn("ai.progress", event.to_dict())
            except Exception:
                pass

    def emit_stage_start(
        self,
        session_id: str,
        stage: str,
        total_stages: int,
        current_stage: int,
    ) -> None:
        """Emit a stage start event."""
        progress = current_stage / total_stages
        self.emit(
            session_id=session_id,
            stage=stage,
            progress=progress,
            message=f"Starting stage: {stage}",
            metadata={"total_stages": total_stages, "current_stage": current_stage},
        )

    def emit_stage_complete(
        self,
        session_id: str,
        stage: str,
        total_stages: int,
        current_stage: int,
    ) -> None:
        """Emit a stage completion event."""
        progress = (current_stage + 1) / total_stages
        self.emit(
            session_id=session_id,
            stage=stage,
            progress=progress,
            message=f"Completed stage: {stage}",
            metadata={"total_stages": total_stages, "current_stage": current_stage},
        )

    def emit_error(
        self,
        session_id: str,
        stage: str,
        error: str,
    ) -> None:
        """Emit an error event."""
        self.emit(
            session_id=session_id,
            stage=stage,
            progress=0.0,
            message=f"Error in stage {stage}: {error}",
            metadata={"error": True, "error_message": error},
        )

    def emit_completion(
        self,
        session_id: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        """Emit a completion event."""
        self.emit(
            session_id=session_id,
            stage="completed",
            progress=1.0,
            message="Workflow completed successfully",
            metadata={"result": result},
        )
