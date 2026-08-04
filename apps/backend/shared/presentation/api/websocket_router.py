"""WebSocket endpoint for real-time events."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from shared.infrastructure.websocket.manager import get_connection_manager
from shared.infrastructure.process.logging_config import get_logger

log = get_logger("websocket")
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time event streaming."""
    manager = get_connection_manager()
    rooms: set[str] = set()

    # Accept connection without a room initially
    await ws.accept()

    try:
        while True:
            data = await ws.receive_json()
            event_type = data.get("type", "")
            room = data.get("room", "")

            if event_type == "watch" and room:
                rooms.add(room)
                manager.join_room(ws, room)
                log.info("ws.watch", room=room)

            elif event_type == "unwatch" and room:
                rooms.discard(room)
                manager.leave_room(ws, room)

            elif event_type == "cancel_job":
                job_id = data.get("id")
                if job_id:
                    from dependencies import get_session_sync
                    session = get_session_sync()
                    try:
                        from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
                        repo = SQLAlchemyJobRepository(session)
                        repo.update_status(str(job_id), "cancelled")
                    finally:
                        session.close()

            elif event_type == "reset_job":
                job_id = data.get("id")
                if job_id:
                    from dependencies import get_session_sync
                    session = get_session_sync()
                    try:
                        from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
                        repo = SQLAlchemyJobRepository(session)
                        repo.reset_steps(str(job_id))
                    finally:
                        session.close()

    except WebSocketDisconnect:
        for room in rooms:
            manager.leave_room(ws, room)
