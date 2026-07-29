"""
Status broadcasting — delivers real-time updates via SocketIO + DB.

Observer pattern: multiple listeners (SocketIO rooms, DB writes)
receive the same domain events.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional, List, Callable

from .interfaces import IBroadcaster
from .models import StatusUpdate, LogEntry, ProcessingComplete, ProcessingError

logger = logging.getLogger(__name__)


class Broadcaster(IBroadcaster):
    """Broadcasts processing status to connected clients.

    Writes to DB (via repository callbacks) AND emits via SocketIO.
    Falls back gracefully if SocketIO not available.
    """

    def __init__(self):
        self._socketio = None
        self._listeners: List[Callable] = []

    def set_socketio(self, socketio) -> None:
        self._socketio = socketio

    def add_listener(self, listener: Callable) -> None:
        """Register an external listener (e.g. DB write callback)."""
        self._listeners.append(listener)

    def _emit(self, event: str, data: dict, room: Optional[str] = None) -> None:
        if not self._socketio:
            return

        async def _send():
            if room:
                await self._socketio.emit(event, data, room=room)
            else:
                await self._socketio.emit(event, data)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(_send())
            else:
                loop.run_until_complete(_send())
        except RuntimeError:
            asyncio.run(_send())
        except Exception as e:
            logger.debug(f"[broadcaster] SocketIO emit failed: {e}")

    def _notify_listeners(self, event_type: str, data: dict) -> None:
        for listener in self._listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.debug(f"[broadcaster] Listener failed: {e}")

    def _room_for(self, table: str, pid: int) -> str:
        if table == 'pending_generations':
            return f'generation_{pid}'
        return f'{"pending" if table == "pending_jobs" else "company"}_{pid}'

    def _prefix(self, table: str) -> str:
        if table == 'pending_generations':
            return 'generation'
        return 'pending' if table == 'pending_jobs' else 'company'

    def step_update(self, event: StatusUpdate) -> None:
        room = self._room_for(event.table, event.pid)
        prefix = self._prefix(event.table)
        data = {
            'id': event.pid, 'step': event.step, 'val': event.val,
            'status': event.status, 'error': event.error, 'ts': event.ts,
        }
        if event.extra:
            data.update(event.extra)
        logger.info(f"[ws] {prefix}:update id={event.pid} step={event.step} val={event.val}")
        self._emit(f'{prefix}:update', data, room=room)
        self._notify_listeners('step_update', data)

    def log(self, event: LogEntry) -> None:
        room = self._room_for(event.table, event.pid)
        prefix = self._prefix(event.table)
        data = {'id': event.pid, 'step': event.step, 'msg': event.msg, 'ts': event.ts}
        logger.info(f"[ws] {prefix}:log id={event.pid} step={event.step} msg={event.msg[:300]}")
        self._emit(f'{prefix}:log', data, room=room)
        self._notify_listeners('log', data)

    def complete(self, event: ProcessingComplete) -> None:
        room = self._room_for(event.table, event.pid)
        prefix = self._prefix(event.table)
        data = {'id': event.pid, **event.result, 'ts': event.ts}
        logger.info(f"[ws] {prefix}:complete id={event.pid} result={event.result}")
        self._emit(f'{prefix}:complete', data, room=room)
        self._notify_listeners('complete', data)

    def error(self, event: ProcessingError) -> None:
        room = self._room_for(event.table, event.pid)
        prefix = self._prefix(event.table)
        error_msg = f"[{event.step}] {event.msg}" if event.step else event.msg
        data = {'id': event.pid, 'msg': error_msg, 'step': event.step, 'ts': event.ts}
        logger.error(f"[ws] {prefix}:error id={event.pid} step={event.step} msg={event.msg[:300]}")
        self._emit(f'{prefix}:error', data, room=room)
        self._notify_listeners('error', data)

    def queue_status(self, processing: int, queued: int, pending: int, concurrency: int) -> None:
        data = {
            'processing': processing, 'queued': queued,
            'pending': pending, 'concurrency': concurrency,
        }
        self._emit('queue:status', data)
        self._notify_listeners('queue_status', data)

    def progress(self, event: Any) -> None:
        room = self._room_for(event.table, event.pid)
        prefix = self._prefix(event.table)
        data = {
            'id': event.pid,
            'status': event.status,
            'current_node': event.current_node,
            'progress_pct': event.progress_pct,
            'message': event.message,
            'completed_nodes': event.completed_nodes,
            'ts': event.ts,
        }
        self._emit(f'{prefix}:progress', data, room=room)
        self._notify_listeners('progress', data)
