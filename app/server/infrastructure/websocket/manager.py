"""WebSocket connection manager for real-time event streaming."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections by room.

    Provides the same room-based broadcasting as Flask-SocketIO
    but uses FastAPI's native WebSocket support.
    """

    def __init__(self):
        self.active: dict[str, set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, room: str = "") -> None:
        """Accept a WebSocket connection and optionally join a room."""
        await ws.accept()
        if room:
            self.active.setdefault(room, set()).add(ws)
        logger.info("ws.connected room=%s", room)

    def disconnect(self, ws: WebSocket, room: str = "") -> None:
        """Remove a WebSocket connection from a room."""
        if room and room in self.active:
            self.active[room].discard(ws)
            if not self.active[room]:
                del self.active[room]
        logger.info("ws.disconnected room=%s", room)

    def join_room(self, ws: WebSocket, room: str) -> None:
        """Add a WebSocket to a room."""
        self.active.setdefault(room, set()).add(ws)
        logger.info("ws.join room=%s", room)

    def leave_room(self, ws: WebSocket, room: str) -> None:
        """Remove a WebSocket from a room."""
        if room in self.active:
            self.active[room].discard(ws)
            if not self.active[room]:
                del self.active[room]

    async def broadcast(self, room: str, data: dict[str, Any]) -> None:
        """Send a message to all connections in a room."""
        if room not in self.active:
            return

        disconnected: list[WebSocket] = []
        for ws in self.active[room]:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)

        # Clean up disconnected clients
        for ws in disconnected:
            self.active[room].discard(ws)

    async def broadcast_all(self, data: dict[str, Any]) -> None:
        """Send a message to all connected clients."""
        for room in list(self.active.keys()):
            await self.broadcast(room, data)


# Global instance
_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
