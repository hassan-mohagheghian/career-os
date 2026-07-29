"""ARQ worker entrypoint — runs background workers.

Usage:
    python -m background.entrypoint

Environment variables:
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD — Redis connection
    WORKER_CONCURRENCY — number of concurrent worker processes
    WORKER_MAX_RETRIES — max retry attempts per job
    WORKER_JOB_TIMEOUT — job timeout in seconds
"""

import os
import sys

# Add server dir to path so bare imports (shared.*, jobs.*, etc.) work
_server_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "server")
)
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

import asyncio

from arq import create_pool
from arq.worker import Worker as ArqWorker

from background.config.settings import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    WORKER_CONCURRENCY,
    WORKER_POLL_INTERVAL,
    WORKER_BURST,
    MAX_RETRIES,
    JOB_TIMEOUT,
    LOG_LEVEL,
)
from background.queue.arq_queue import FUNCTIONS, redis_settings
from background.telemetry.logging import init_logging


init_logging(level=LOG_LEVEL)


async def create_worker() -> ArqWorker:
    pool = await create_pool(redis_settings())

    async def shutdown(ctx: dict) -> None:
        await pool.aclose()

    worker = ArqWorker(
        redis_pool=pool,
        functions=FUNCTIONS,
        max_jobs=WORKER_CONCURRENCY,
        poll_delay=WORKER_POLL_INTERVAL,
        burst=WORKER_BURST,
        max_tries=MAX_RETRIES,
        job_timeout=JOB_TIMEOUT,
        on_shutdown=shutdown,
    )
    return worker


async def main():
    worker = await create_worker()
    await worker.async_run()


if __name__ == "__main__":
    asyncio.run(main())
