"""Background application settings — environment-driven configuration."""

import os

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")

REDIS_URL = f"redis://{':' + REDIS_PASSWORD + '@' if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}"

QUEUE_NAME = os.environ.get("ARQ_QUEUE_NAME", "arq:queue")
QUEUE_GROUP = os.environ.get("ARQ_QUEUE_GROUP", "job-search")

WORKER_CONCURRENCY = int(os.environ.get("WORKER_CONCURRENCY", "4"))
WORKER_POLL_INTERVAL = float(os.environ.get("WORKER_POLL_INTERVAL", "0.5"))
WORKER_BURST = os.environ.get("WORKER_BURST", "0") == "1"

MAX_RETRIES = int(os.environ.get("WORKER_MAX_RETRIES", "3"))
RETRY_BACKOFF = float(os.environ.get("WORKER_RETRY_BACKOFF", "10.0"))
JOB_TIMEOUT = int(os.environ.get("WORKER_JOB_TIMEOUT", "600"))

LOG_LEVEL = os.environ.get("WORKER_LOG_LEVEL", "INFO")

# Database — reuses the same DB as the server
DB_PATH = os.environ.get("DB_PATH", "app/server/db/jobs.db")
SERVER_DIR = os.environ.get("SERVER_DIR", "")
