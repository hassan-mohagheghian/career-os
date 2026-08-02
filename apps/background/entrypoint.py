"""TaskIQ worker entrypoint — runs background workers.

Usage:
    python -m background.main
    BACKGROUND_WORKER=true python app/start.py dev

The worker consumes the RedisStreamBroker declared in
`shared.infrastructure.taskiq.config` and executes the tasks defined in
`shared.infrastructure.taskiq.tasks`.

Environment variables:
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD — Redis connection
    WORKER_CONCURRENCY — number of concurrent worker processes
    WORKER_MAX_RETRIES — max retry attempts per task
    WORKER_JOB_TIMEOUT — task timeout in seconds
"""

import os
import sys

# Add server dir to path so bare imports (shared.*, jobs.*, etc.) work
_server_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "server")
)
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from taskiq.cli.worker.args import WorkerArgs, LogLevel
from taskiq.cli.worker.run import run_worker

from shared.infrastructure.taskiq.config import (
    WORKER_CONCURRENCY,
    LOG_LEVEL,
)

BROKER = "shared.infrastructure.taskiq.config:broker"
TASK_MODULES = ["shared.infrastructure.taskiq.tasks"]


def create_worker_args() -> WorkerArgs:
    return WorkerArgs(
        broker=BROKER,
        modules=TASK_MODULES,
        app_dir=_server_dir,
        configure_logging=True,
        log_level=LogLevel[LOG_LEVEL.upper()],
        workers=WORKER_CONCURRENCY,
    )


def main() -> None:
    run_worker(create_worker_args())


if __name__ == "__main__":
    main()
