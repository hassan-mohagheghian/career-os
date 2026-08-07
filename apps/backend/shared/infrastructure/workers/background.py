"""Background task management for FastAPI.

Provides async task execution for long-running operations like
job processing, company analysis, and insights generation.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine

from shared.infrastructure.process.logging_config import get_logger
logger = get_logger('workers.background')


class BackgroundTaskManager:
    """Manages background tasks for the application.

    Wraps asyncio tasks with tracking and error handling.
    """

    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}

    async def run(
        self,
        task_id: str,
        coro: Coroutine,
        name: str | None = None,
    ) -> asyncio.Task:
        """Run a coroutine as a background task."""
        if task_id in self._tasks and not self._tasks[task_id].done():
            logger.warning("Task %s already running", task_id)
            coro.close()
            return self._tasks[task_id]

        task = asyncio.create_task(coro, name=name or task_id)
        self._tasks[task_id] = task

        # Clean up when done
        task.add_done_callback(lambda t: self._cleanup(task_id, t))

        logger.info("Started background task: %s", task_id)
        return task

    def _cleanup(self, task_id: str, task: asyncio.Task) -> None:
        """Clean up completed task."""
        self._tasks.pop(task_id, None)
        if task.exception():
            logger.error("Background task %s failed: %s", task_id, task.exception())
        else:
            logger.info("Background task %s completed", task_id)

    def cancel(self, task_id: str) -> bool:
        """Cancel a running task."""
        task = self._tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            logger.info("Cancelled background task: %s", task_id)
            return True
        return False

    def is_running(self, task_id: str) -> bool:
        """Check if a task is running."""
        task = self._tasks.get(task_id)
        return task is not None and not task.done()

    @property
    def running_tasks(self) -> list[str]:
        """Get list of running task IDs."""
        return [tid for tid, t in self._tasks.items() if not t.done()]


# Global instance
_manager: BackgroundTaskManager | None = None


def get_task_manager() -> BackgroundTaskManager:
    """Get the global background task manager."""
    global _manager
    if _manager is None:
        _manager = BackgroundTaskManager()
    return _manager
