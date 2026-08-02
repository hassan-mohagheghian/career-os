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

from taskiq.cli.worker.args import LogLevel, WorkerArgs
from taskiq.cli.worker.run import run_worker

from shared.infrastructure.taskiq.config import LOG_LEVEL, WORKER_CONCURRENCY

BROKER = "shared.infrastructure.taskiq.config:broker"
TASK_MODULES = ["shared.infrastructure.taskiq.tasks"]

APP_DIR = "apps.backend"


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
    run_worker(create_worker_args())


if __name__ == "__main__":
    main()