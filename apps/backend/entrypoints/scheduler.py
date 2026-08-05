"""TaskIQ scheduler for periodic background tasks.

Usage:
    python -m taskiq scheduler \
        apps.backend.entrypoints.scheduler:create_scheduler \
        shared.infrastructure.taskiq.tasks

Schedules are attached to tasks via the `schedule` label and collected by the
`LabelScheduleSource` at startup (see docs/queue/processing/taskiq-processing.md).
Currently only ``periodic_db_backup`` carries a schedule (see
``DB_BACKUP_INTERVAL_MINUTES`` in .env).
"""

from __future__ import annotations

from taskiq.scheduler.scheduler import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from shared.infrastructure.taskiq.config import broker
from shared.infrastructure.taskiq.tasks import (  # noqa: F401  (register tasks on broker)
    periodic_db_backup,
    process_company_task,
    process_execution_task,
    process_generation_task,
)


def create_scheduler() -> TaskiqScheduler:
    return TaskiqScheduler(broker, [LabelScheduleSource(broker)])


if __name__ == "__main__":
    import asyncio

    asyncio.run(create_scheduler())
