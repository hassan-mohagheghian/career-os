"""Processing event publisher.

Publishes ProcessingExecution lifecycle events over Redis pub/sub so that the
API server's SSE endpoints can stream them to frontend clients.

Event flow (per docs/domain/processing/events.md):

    ProcessingExecution update
        ↓
    Domain event
        ↓
    Event handler
        ↓
    SSE endpoint
        ↓
    Frontend client

TaskIQ does not produce these events directly. The worker updates the
ProcessingExecution and publishes a domain event; SSE only consumes it.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, UTC
from typing import Any

import redis.asyncio as aioredis

from shared.infrastructure.process.logging_config import get_logger

log = get_logger("processing.events")

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")

CHANNEL_PREFIX = "processing:events"
CHANNEL_PATTERN = f"{CHANNEL_PREFIX}:*"

# Event names emitted over SSE (matches the frontend useProcessingEvents hook).
EXECUTION_QUEUED = "ExecutionQueued"
EXECUTION_STARTED = "ExecutionStarted"
EXECUTION_STEP_CHANGED = "ExecutionStepChanged"
EXECUTION_COMPLETED = "ExecutionCompleted"
EXECUTION_FAILED = "ExecutionFailed"

# Job Context Preparation workflow events (consumed by SSE + frontend).
CONTEXT_STARTED = "processing.started"
CONTEXT_LOADING_JOB = "processing.loading_job"
CONTEXT_FETCHING_SOURCES = "processing.fetching_sources"
CONTEXT_EXTRACTING_CONTENT = "processing.extracting_content"
CONTEXT_READY = "processing.context_ready"
CONTEXT_FAILED = "processing.failed"


def _redis_url() -> str:
    auth = f":{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
    return f"redis://{auth}{REDIS_HOST}:{REDIS_PORT}"


def execution_channel(execution_id: str) -> str:
    return f"{CHANNEL_PREFIX}:{execution_id}"


def build_event(
    event_name: str,
    execution_id: str,
    job_id: str | None,
    status: str,
    current_step: str | None = None,
    progress: float | None = None,
    message: str | None = None,
    updated_at: str | None = None,
) -> dict[str, Any]:
    """Build the wire event in the format the SSE endpoint and frontend expect."""
    return {
        "event": event_name,
        "data": {
            "execution_id": execution_id,
            "job_id": job_id,
            "status": status,
            "current_step": current_step,
            "progress": progress,
            "message": message,
            "updated_at": updated_at or datetime.now(UTC).isoformat(),
        },
    }


async def publish(
    event_name: str,
    execution_id: str,
    job_id: str | None,
    status: str,
    **kwargs: Any,
) -> None:
    """Publish a processing event to Redis pub/sub.

    Publishing is best-effort: if Redis is unavailable the event is dropped
    (lifecycle state remains the source of truth in PostgreSQL).
    """
    event = build_event(event_name, execution_id, job_id, status, **kwargs)
    try:
        redis = aioredis.from_url(_redis_url(), socket_connect_timeout=2)
        try:
            await redis.publish(execution_channel(execution_id), json.dumps(event))
        finally:
            await redis.aclose()
    except Exception as e:
        log.debug("processing.event.publish_failed", error=str(e), event=event_name)


def publish_sync(
    event_name: str,
    execution_id: str,
    job_id: str | None,
    status: str,
    **kwargs: Any,
) -> None:
    """Synchronous wrapper used from sync API handlers."""
    asyncio.run(publish(event_name, execution_id, job_id, status, **kwargs))
