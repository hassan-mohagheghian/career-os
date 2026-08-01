"""ProcessingExecution REST + SSE API.

- GET /api/processing/executions              → list executions
- GET /api/processing/executions/{id}         → get one execution
- GET /api/processing/{execution_id}/events   → SSE stream for one execution

The API does not expose TaskIQ concepts to clients.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from dependencies import get_processing_execution_repo
from processing.infrastructure import SQLAlchemyProcessingExecutionRepository
from shared.application.exceptions import NotFoundError
from shared.infrastructure.events.processing_events import execution_channel
from shared.infrastructure.events.sse import stream_channel

router = APIRouter()


def _execution_to_dict(execution) -> dict:
    return execution.to_dict()


@router.get("/executions")
def list_executions(
    limit: int = 50,
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    executions = exec_repo.list_recent(limit=limit)
    return [_execution_to_dict(e) for e in executions]


@router.get("/executions/{execution_id}")
def get_execution(
    execution_id: str,
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    execution = exec_repo.get_by_id(execution_id)
    if not execution:
        raise NotFoundError(f"ProcessingExecution {execution_id} not found")
    return _execution_to_dict(execution)


@router.get("/{execution_id}/events")
async def execution_events(
    execution_id: str,
    request: Request,
    exec_repo: SQLAlchemyProcessingExecutionRepository = Depends(get_processing_execution_repo),
):
    execution = exec_repo.get_by_id(execution_id)
    if not execution:
        raise NotFoundError(f"ProcessingExecution {execution_id} not found")

    channel = execution_channel(execution_id)

    async def event_stream():
        async for chunk in stream_channel(channel):
            if await request.is_disconnected():
                break
            yield chunk
        # Keep the connection open for late events
        while not await request.is_disconnected():
            await asyncio.sleep(15)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
