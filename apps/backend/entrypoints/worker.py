"""TaskIQ worker entrypoint — runs background workers.

Usage:
    python -m apps.backend.entrypoints.worker
    BACKGROUND_WORKER=true python apps/start.py dev

The worker consumes the RedisStreamBroker declared in
`shared.infrastructure.taskiq.config` and executes the tasks defined in
`shared.infrastructure.taskiq.tasks`.

Environment variables:
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD — Redis connection
    WORKER_CONCURRENCY — number of concurrent worker processes
    WORKER_LOG_LEVEL — worker log level
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

load_dotenv()  # noqa: E402 — must run before taskiq/config imports read env

from taskiq.cli.worker.args import LogLevel, WorkerArgs  # noqa: E402
from taskiq.cli.worker.run import run_worker  # noqa: E402

from shared.infrastructure.taskiq.config import LOG_LEVEL, WORKER_CONCURRENCY  # noqa: E402
from shared.infrastructure.process.logging_config import get_logger  # noqa: E402

BROKER = "shared.infrastructure.taskiq.config:broker"
TASK_MODULES = ["shared.infrastructure.taskiq.tasks"]

APP_DIR = "apps.backend"

log = get_logger("worker.startup")


def create_worker_args() -> WorkerArgs:
    return WorkerArgs(
        broker=BROKER,
        modules=TASK_MODULES,
        app_dir=APP_DIR,
        configure_logging=True,
        log_level=LogLevel[LOG_LEVEL.upper()],
        workers=WORKER_CONCURRENCY,
    )


def main() -> None:
    log.info(
        "worker.startup",
        workers=WORKER_CONCURRENCY,
        broker=BROKER,
        modules=TASK_MODULES,
    )
    print(
        f"[worker] Starting {WORKER_CONCURRENCY} worker processes (broker={BROKER})",
        file=sys.stderr,
    )
    run_worker(create_worker_args())


if __name__ == "__main__":
    main()
