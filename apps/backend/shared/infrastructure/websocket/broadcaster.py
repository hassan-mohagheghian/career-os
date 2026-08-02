"""WebSocket broadcaster adapter.

Bridges the existing Broadcaster interface to SocketIO connections.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional

from shared.infrastructure.process.logging_config import get_logger
logger = get_logger('websocket.broadcaster')

# SocketIO server instance (set during app initialization)
_socketio_server = None


def set_socketio_server(server) -> None:
    """Set the SocketIO server instance for broadcasting."""
    global _socketio_server
    _socketio_server = server


def get_socketio_server():
    """Get the SocketIO server instance."""
    return _socketio_server


class WebSocketBroadcaster:
    """Broadcasts events via SocketIO connections.

    Implements the same interface as the original Flask-SocketIO broadcaster
    but uses python-socketio's async server.
    """

    def __init__(self):
        self._listeners: list[Callable] = []

    def set_socketio(self, socketio_server) -> None:
        """Set the SocketIO server (for backward compatibility)."""
        set_socketio_server(socketio_server)

    def add_listener(self, listener: Callable) -> None:
        """Register an external listener."""
        self._listeners.append(listener)

    def _emit(self, event: str, data: dict[str, Any], room: Optional[str] = None) -> None:
        """Emit an event via SocketIO."""
        server = _socketio_server
        if not server:
            logger.debug("SocketIO server not available, skipping emit")
            return

        async def _send():
            if room:
                await server.emit(event, data, room=room)
            else:
                await server.emit(event, data)

        # Schedule the broadcast in the event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(_send())
            else:
                loop.run_until_complete(_send())
        except RuntimeError:
            # No event loop running, create one
            asyncio.run(_send())

    def _notify_listeners(self, event_type: str, data: dict[str, Any]) -> None:
        """Notify registered listeners."""
        for listener in self._listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.debug("Listener failed: %s", e)

    def _room_for(self, entity_type: str, pid: Any) -> str:
        """Get room name for an entity_type/pid combination."""
        if entity_type == "generation":
            return f"generation_{pid}"
        return f'{entity_type}_{pid}'

    def _prefix(self, entity_type: str) -> str:
        """Get event prefix for an entity type."""
        if entity_type == "generation":
            return "generation"
        return "job" if entity_type == "job" else "company"

    def step_update(self, event: Any) -> None:
        """Broadcast a step update event."""
        room = self._room_for(event.entity_type, event.pid)
        prefix = self._prefix(event.entity_type)
        data = {
            "id": event.pid,
            "step": event.step,
            "val": event.val,
            "status": event.status,
            "error": event.error,
            "ts": event.ts,
        }
        if hasattr(event, 'extra') and event.extra:
            data.update(event.extra)
        logger.info("ws.%s:update id=%s step=%s val=%s", prefix, event.pid, event.step, event.val)
        self._emit(f"{prefix}:update", data, room=room)
        self._notify_listeners("step_update", data)

    def log(self, event: Any) -> None:
        """Broadcast a log event."""
        room = self._room_for(event.entity_type, event.pid)
        prefix = self._prefix(event.entity_type)
        data = {"id": event.pid, "step": event.step, "msg": event.msg, "ts": event.ts}
        logger.info("ws.%s:log id=%s step=%s msg=%s", prefix, event.pid, event.step, event.msg[:80])
        self._emit(f"{prefix}:log", data, room=room)
        self._notify_listeners("log", data)

    def complete(self, event: Any) -> None:
        """Broadcast a completion event."""
        room = self._room_for(event.entity_type, event.pid)
        prefix = self._prefix(event.entity_type)
        data = {"id": event.pid, **event.result, "ts": event.ts}
        logger.info("ws.%s:complete id=%s result=%s", prefix, event.pid, event.result)
        self._emit(f"{prefix}:complete", data, room=room)
        self._notify_listeners("complete", data)

    def error(self, event: Any) -> None:
        """Broadcast an error event."""
        room = self._room_for(event.entity_type, event.pid)
        prefix = self._prefix(event.entity_type)
        error_msg = f"[{event.step}] {event.msg}" if event.step else event.msg
        data = {"id": event.pid, "msg": error_msg, "step": event.step, "ts": event.ts}
        logger.error("ws.%s:error id=%s step=%s msg=%s", prefix, event.pid, event.step, event.msg[:80])
        self._emit(f"{prefix}:error", data, room=room)
        self._notify_listeners("error", data)

    def queue_status(self, processing: int, queued: int, pending: int, concurrency: int) -> None:
        """Broadcast queue status update."""
        data = {
            "processing": processing,
            "queued": queued,
            "pending": pending,
            "concurrency": concurrency,
        }
        self._emit("queue:status", data)
        self._notify_listeners("queue_status", data)

    def progress(self, event: Any) -> None:
        """Broadcast workflow progress update."""
        room = self._room_for(event.entity_type, event.pid)
        prefix = self._prefix(event.entity_type)
        data = {
            "id": event.pid,
            "status": event.status,
            "current_node": event.current_node,
            "progress_pct": event.progress_pct,
            "message": event.message,
            "completed_nodes": event.completed_nodes,
            "ts": event.ts,
        }
        logger.info("ws.%s:progress id=%s node=%s pct=%s", prefix, event.pid, event.current_node, event.progress_pct)
        self._emit(f"{prefix}:progress", data, room=room)
        self._notify_listeners("progress", data)
