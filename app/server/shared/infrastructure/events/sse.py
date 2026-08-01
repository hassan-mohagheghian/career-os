"""SSE stream helpers for processing events.

Consumes ProcessingExecution lifecycle events from Redis pub/sub and formats
them as Server-Sent Events for frontend clients.

SSE is a consumer only — it never creates domain events. See
docs/api/sse/processing-events.md.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import redis.asyncio as aioredis

from shared.infrastructure.events.processing_events import _redis_url


async def stream_channel(channel: str) -> AsyncIterator[str]:
    """Yield SSE-formatted events published to a single Redis channel."""
    redis = aioredis.from_url(_redis_url(), socket_connect_timeout=2)
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                payload = json.loads(message["data"])
            except (TypeError, ValueError):
                continue
            event_name = payload.get("event", "")
            data = json.dumps(payload.get("data", {}), default=str)
            yield f"event: {event_name}\ndata: {data}\n\n"
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


async def stream_pattern(pattern: str) -> AsyncIterator[str]:
    """Yield SSE-formatted events published to channels matching a pattern."""
    redis = aioredis.from_url(_redis_url(), socket_connect_timeout=2)
    pubsub = redis.pubsub()
    await pubsub.psubscribe(pattern)
    try:
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            try:
                payload = json.loads(message["data"])
            except (TypeError, ValueError):
                continue
            event_name = payload.get("event", "")
            data = json.dumps(payload.get("data", {}), default=str)
            yield f"event: {event_name}\ndata: {data}\n\n"
    finally:
        await pubsub.punsubscribe(pattern)
        await pubsub.aclose()
