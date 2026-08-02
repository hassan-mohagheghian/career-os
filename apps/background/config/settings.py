"""Background application settings — environment-driven configuration.

Re-exports the TaskIQ broker configuration from the server's shared
infrastructure so the background worker and scheduler stay consistent
with the API server.

Environment variables:
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD — Redis connection
    WORKER_CONCURRENCY — number of concurrent worker processes
    WORKER_MAX_RETRIES — max retry attempts per task
    WORKER_JOB_TIMEOUT — task timeout in seconds
    WORKER_LOG_LEVEL — worker log level
"""

import os
import sys

_server_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "server")
)
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from shared.infrastructure.taskiq.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    REDIS_URL,
    QUEUE_NAME,
    WORKER_CONCURRENCY,
    WORKER_MAX_RETRIES,
    WORKER_RETRY_BACKOFF,
    WORKER_JOB_TIMEOUT,
    LOG_LEVEL,
)

# Database — reuses the same DB as the server
DB_PATH = os.environ.get("DB_PATH", "apps/backend/db/jobs.db")
SERVER_DIR = os.environ.get("SERVER_DIR", "")

__all__ = [
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_PASSWORD",
    "REDIS_URL",
    "QUEUE_NAME",
    "WORKER_CONCURRENCY",
    "WORKER_MAX_RETRIES",
    "WORKER_RETRY_BACKOFF",
    "WORKER_JOB_TIMEOUT",
    "LOG_LEVEL",
    "DB_PATH",
    "SERVER_DIR",
]
