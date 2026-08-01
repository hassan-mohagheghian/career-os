"""Processing event publisher.

Publishes ProcessingExecution lifecycle + workflow progress events over Redis
pub/sub so that the API server's SSE endpoints can stream them to frontend
clients.

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
import uuid
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

# ── Execution lifecycle events (user-facing) ────────────────────────────
EXECUTION_CREATED = "execution.created"
EXECUTION_STARTED = "execution.started"
EXECUTION_COMPLETED = "execution.completed"
EXECUTION_FAILED = "execution.failed"
EXECUTION_CANCELLED = "execution.cancelled"

# ── Workflow progress events (user-facing) ──────────────────────────────
WORKFLOW_STEP_STARTED = "workflow.step.started"
WORKFLOW_STEP_PROGRESS = "workflow.step.progress"
WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
WORKFLOW_STEP_FAILED = "workflow.step.failed"

# ── Queue events (user-facing) ──────────────────────────────────────────
QUEUE_ENTRY_REMOVED = "queue.entry.removed"


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
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the wire event in the format the SSE endpoint and frontend expect.

    The outer envelope ``{"event": ..., "data": ...}`` is the Redis pub/sub
    message. ``data`` is the SSE payload with a stable public contract:

    {id, type, timestamp, job_id, execution_id, payload}
    """
    payload: dict[str, Any] = {"status": status}
    payload.update(kwargs)
    return {
        "event": event_name,
        "data": {
            "id": str(uuid.uuid4()),
            "type": event_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "job_id": job_id,
            "execution_id": execution_id,
            "payload": payload,
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
