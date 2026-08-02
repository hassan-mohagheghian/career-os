"""TaskIQ scheduler for periodic background tasks.

Usage:
    python -m apps.backend.entrypoints.scheduler

Schedules are attached to tasks via the `schedule` label and collected by the
`LabelScheduleSource` at startup (see docs/queue/processing/taskiq-processing.md).
"""

from __future__ import annotations

from taskiq.scheduler.scheduler import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.taskiq.config import broker
from shared.infrastructure.taskiq.tasks import (  # noqa: F401  (register tasks on broker)
    process_company_task,
    process_execution_task,
    process_generation_task,
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

    from shared.infrastructure.database.session import get_session_sync
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
    except Exception as e:  # noqa: BLE001
        log.error("scheduler.cleanup.failed", error=str(e))


def create_scheduler() -> TaskiqScheduler:
    return TaskiqScheduler(broker, [LabelScheduleSource(broker)])


if __name__ == "__main__":
    import asyncio

    asyncio.run(create_scheduler())