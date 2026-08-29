"""TaskIQ broker configuration.

The TaskIQ broker is the infrastructure layer responsible for background
task dispatch, worker communication, and retry handling.

Redis is used only as the TaskIQ message broker. It does not store business
state or workflow state — that belongs to PostgreSQL and LangGraph checkpoints.
"""

from __future__ import annotations

import os

from taskiq import AsyncBroker, InMemoryBroker
from taskiq_redis import RedisStreamBroker

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")

QUEUE_NAME = os.environ.get("TASKIQ_QUEUE_NAME", "taskiq:queue")


def _redis_url() -> str:
    auth = f":{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
    return f"redis://{auth}{REDIS_HOST}:{REDIS_PORT}"


REDIS_URL = _redis_url()

# Retry behavior for infrastructure failures (worker crash, Redis unavailable,
# temporary network failures). Workflow failures are handled separately by
# LangGraph checkpointing and ProcessingExecution state management.
WORKER_CONCURRENCY = int(os.environ.get("WORKER_CONCURRENCY", "4"))
WORKER_MAX_RETRIES = int(os.environ.get("WORKER_MAX_RETRIES", "3"))
WORKER_RETRY_BACKOFF = float(os.environ.get("WORKER_RETRY_BACKOFF", "10.0"))
WORKER_JOB_TIMEOUT = int(os.environ.get("WORKER_JOB_TIMEOUT", "600"))

# How often `reconcile_stuck_executions` runs to detect dead / long-running
# workers (seconds). Exposed so operators can tune sweep cadence without a deploy.
RECONCILE_INTERVAL_SECONDS = int(os.environ.get("RECONCILE_INTERVAL_SECONDS", "30"))

LOG_LEVEL = os.environ.get("WORKER_LOG_LEVEL", "INFO")


def build_broker() -> AsyncBroker:
    """Build the TaskIQ broker.

    Returns an in-memory broker when `TASKIQ_BROKER=memory` (used in tests),
    otherwise a Redis Streams broker.
    """
    if os.environ.get("TASKIQ_BROKER", "").lower() in ("memory", "inmemory"):
        return InMemoryBroker()
    return RedisStreamBroker(
        _redis_url(),
        queue_name=QUEUE_NAME,
    )


broker = build_broker()
