"""TaskIQ scheduler for periodic background tasks.

Usage:
    python -m taskiq scheduler \
        apps.backend.entrypoints.scheduler:create_scheduler \
        shared.infrastructure.taskiq.tasks

Schedules are attached to tasks via the `schedule` label and collected by the
`LabelScheduleSource` at startup (see docs/queue/processing/taskiq-processing.md).

Scheduled tasks:
- ``periodic_db_backup``       → periodic PostgreSQL backup (see ``DB_BACKUP_INTERVAL_MINUTES``)
- ``reconcile_stuck_executions`` → every 30s sweep to recover stuck QUEUED/RUNNING executions
"""

from __future__ import annotations

from taskiq.scheduler.scheduler import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from shared.infrastructure.taskiq.config import broker
from shared.infrastructure.taskiq.tasks import (  # noqa: F401  (register tasks on broker)
    periodic_db_backup,
    process_execution_task,
    reconcile_stuck_executions,
)


def create_scheduler() -> TaskiqScheduler:
    return TaskiqScheduler(broker, [LabelScheduleSource(broker)])


if __name__ == "__main__":
    import asyncio

    asyncio.run(create_scheduler())
