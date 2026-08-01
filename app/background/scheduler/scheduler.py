"""TaskIQ scheduler for periodic background tasks.

Usage:
    python -m taskiq scheduler \
        --app-dir app/server \
        --skip-first-run \
        background.scheduler.scheduler:create_scheduler \
        shared.infrastructure.taskiq.tasks

Schedules are attached to tasks via the `schedule` label and collected by the
`LabelScheduleSource` at startup (see docs/queue/processing/taskiq-processing.md).
"""

import os
import sys

_server_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "server")
)
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from taskiq.scheduler.scheduler import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from shared.infrastructure.taskiq.config import broker
from shared.infrastructure.taskiq.tasks import (  # noqa: F401  (register tasks on broker)
    process_job_task,
    process_company_task,
    process_generation_task,
    process_execution_task,
)


@broker.task(
    schedule=[
        {
            "cron": "0 * * * *",
            "kwargs": {"hours": 24},
        }
    ]
)
async def periodic_job_cleanup(hours: int = 24) -> None:
    """Periodic cleanup of stale queued items."""
    import asyncio
    from background.infrastructure.database import get_session_sync
    from background.telemetry.logging import get_logger
    from jobs.infrastructure import SQLAlchemyJobRepository

    log = get_logger("scheduler.cleanup")

    def _run() -> int:
        session = get_session_sync()
        try:
            repo = SQLAlchemyJobRepository(session)
            return repo.cleanup_stale_items(hours=hours)
        finally:
            session.close()

    try:
        cleaned = await asyncio.to_thread(_run)
        log.info("scheduler.cleanup.complete", cleaned=cleaned)
    except Exception as e:
        log.error("scheduler.cleanup.failed", error=str(e))


def create_scheduler() -> TaskiqScheduler:
    return TaskiqScheduler(broker, [LabelScheduleSource(broker)])
