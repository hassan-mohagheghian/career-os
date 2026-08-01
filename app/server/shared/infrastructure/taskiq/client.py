"""TaskIQ client for enqueuing background tasks from the API layer.

Provides async and sync helpers that mirror the previous ARQ client API.
Each enqueue call uses a short-lived broker so it is safe to use from both
async code (running in the application event loop) and sync code (running in
a threadpool, where ``asyncio.run`` creates a fresh event loop).
"""

from __future__ import annotations

import asyncio

from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.taskiq.config import build_broker
from shared.infrastructure.taskiq.tasks import (
    process_company_task,
    process_execution_task,
    process_generation_task,
    process_job_task,
)

log = get_logger("taskiq.client")


async def _enqueue(task, *args, **kwargs) -> str | None:
    broker = build_broker()
    await broker.startup()
    try:
        registered = broker.register_task(
            task.original_func, task_name=task.task_name, **task.labels
        )
        message = await registered.kiq(*args, **kwargs)
        log.info("taskiq.enqueued", task=task.task_name)
        return getattr(message, "task_id", None)
    finally:
        await broker.shutdown()


async def enqueue_job(job_id: int) -> str | None:
    """Dispatch a job processing task."""
    return await _enqueue(process_job_task, job_id)


async def enqueue_company(company_id: int) -> str | None:
    """Dispatch a company processing task."""
    return await _enqueue(process_company_task, company_id)


async def enqueue_generation(gen_id: str) -> str | None:
    """Dispatch a resume / cover letter generation task."""
    return await _enqueue(process_generation_task, gen_id)


async def enqueue_execution(execution_id: str) -> str | None:
    """Dispatch a ProcessingExecution task."""
    return await _enqueue(process_execution_task, execution_id)


def enqueue_job_sync(job_id: int) -> str | None:
    return asyncio.run(enqueue_job(job_id))


def enqueue_company_sync(company_id: int) -> str | None:
    return asyncio.run(enqueue_company(company_id))


def enqueue_generation_sync(gen_id: str) -> str | None:
    return asyncio.run(enqueue_generation(gen_id))


def enqueue_execution_sync(execution_id: str) -> str | None:
    return asyncio.run(enqueue_execution(execution_id))
