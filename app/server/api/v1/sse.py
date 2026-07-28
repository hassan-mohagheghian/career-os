"""Server-Sent Events (SSE) endpoints for real-time data streaming."""

import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from dependencies import get_session_sync
from pending.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository

router = APIRouter()


async def _stream_pending_jobs():
    """Stream pending jobs updates via SSE."""
    last_hash = ""
    while True:
        session = get_session_sync()
        try:
            repo = SQLAlchemyPendingRepository(session)
            items = repo.get_all_for_stream("pending_jobs")
            data = json.dumps(items, ensure_ascii=False, default=str)
            current_hash = str(hash(data))
            if current_hash != last_hash:
                last_hash = current_hash
                yield f"data: {data}\n\n"
        finally:
            session.close()
        await asyncio.sleep(2)


async def _stream_pending_companies():
    """Stream pending companies updates via SSE."""
    last_hash = ""
    while True:
        session = get_session_sync()
        try:
            repo = SQLAlchemyPendingRepository(session)
            items = repo.get_all_for_stream("pending_companies")
            data = json.dumps(items, ensure_ascii=False, default=str)
            current_hash = str(hash(data))
            if current_hash != last_hash:
                last_hash = current_hash
                yield f"data: {data}\n\n"
        finally:
            session.close()
        await asyncio.sleep(2)


@router.get("/pending/stream")
async def stream_pending():
    """Stream pending jobs updates via SSE."""
    return StreamingResponse(
        _stream_pending_jobs(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/pending-companies/stream")
async def stream_pending_companies():
    """Stream pending companies updates via SSE."""
    return StreamingResponse(
        _stream_pending_companies(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
