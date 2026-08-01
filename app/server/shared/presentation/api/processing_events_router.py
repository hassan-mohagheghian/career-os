"""Global processing-events SSE router.

Serves a single Server-Sent Event stream at /events/processing that
forwards ProcessingExecution lifecycle events to the frontend.

Registered directly on the app (no /api prefix) — matches the frontend
hook useProcessingEvents() which subscribes to SSE_URL='/events/processing'.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from shared.infrastructure.events.processing_events import CHANNEL_PATTERN
from shared.infrastructure.events.sse import stream_pattern

router = APIRouter()


@router.get("/processing")
async def processing_events(request: Request):
    async def event_stream():
        async for chunk in stream_pattern(CHANNEL_PATTERN):
            if await request.is_disconnected():
                break
            yield chunk
        while not await request.is_disconnected():
            await asyncio.sleep(15)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
