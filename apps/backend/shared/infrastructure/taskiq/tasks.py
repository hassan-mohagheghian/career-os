"""TaskIQ task definitions.

These tasks are thin infrastructure wrappers that coordinate background
execution. They do NOT contain business logic — they delegate to the existing
application services / workers which own the LangGraph workflow execution.

Each task mirrors the previous ARQ task it replaces:

- process_job_task       → replaces ARQ ``process_job``
- process_company_task   → replaces ARQ ``process_company``
- process_generation_task→ replaces ARQ ``process_generation``
- process_execution_task → drives the ProcessingExecution lifecycle through
  the TaskIQ worker → LangGraph workflow flow.
"""

from __future__ import annotations

import asyncio

from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.taskiq.config import (
    broker,
    WORKER_MAX_RETRIES,
    WORKER_RETRY_BACKOFF,
)

log = get_logger("taskiq.tasks")


@broker.task(retry_on_error=True, retry_count=WORKER_MAX_RETRIES, retry_delay=WORKER_RETRY_BACKOFF)
async def process_job_task(job_id: int) -> dict:
    """Process a pending job through the LangGraph job pipeline."""
    log.info("taskiq.task.job.start", job_id=job_id)
    try:
        from jobs.infrastructure.workers.worker import process_job

        await asyncio.to_thread(process_job, job_id)
        log.info("taskiq.task.job.complete", job_id=job_id)
        return {"status": "completed", "job_id": job_id}
    except Exception as e:
        log.error("taskiq.task.job.failed", job_id=job_id, error=str(e))
        raise


@broker.task(retry_on_error=True, retry_count=WORKER_MAX_RETRIES, retry_delay=WORKER_RETRY_BACKOFF)
async def process_company_task(company_id: int) -> dict:
    """Process a pending company through its processing pipeline."""
    log.info("taskiq.task.company.start", company_id=company_id)
    try:
        from companies.infrastructure.workers.company_worker import process_company

        await asyncio.to_thread(process_company, company_id)
        log.info("taskiq.task.company.complete", company_id=company_id)
        return {"status": "completed", "company_id": company_id}
    except Exception as e:
        log.error("taskiq.task.company.failed", company_id=company_id, error=str(e))
        raise


@broker.task(retry_on_error=True, retry_count=WORKER_MAX_RETRIES, retry_delay=WORKER_RETRY_BACKOFF)
async def process_generation_task(gen_id: str) -> dict:
    """Generate a resume / cover letter in the background."""
    log.info("taskiq.task.generation.start", gen_id=gen_id)
    try:
        from jobs.infrastructure.workers.generation_worker import process_generation

        await asyncio.to_thread(process_generation, gen_id)
        log.info("taskiq.task.generation.complete", gen_id=gen_id)
        return {"status": "completed", "gen_id": gen_id}
    except Exception as e:
        log.error("taskiq.task.generation.failed", gen_id=gen_id, error=str(e))
        raise


@broker.task(retry_on_error=True, retry_count=WORKER_MAX_RETRIES, retry_delay=WORKER_RETRY_BACKOFF)
async def process_execution_task(execution_id: str) -> dict:
    """Run a ProcessingExecution through its LangGraph workflow.

    Flow:
    - Load ProcessingExecution
    - Mark execution running
    - Start LangGraph workflow for the execution's target
    - Complete or fail the execution
    """
    log.info("taskiq.task.execution.start", execution_id=execution_id)
    try:
        from processing.infrastructure.runner.execution_runner import ProcessingExecutionRunner

        runner = ProcessingExecutionRunner()
        result = await asyncio.to_thread(runner.run, execution_id)
        log.info("taskiq.task.execution.complete", execution_id=execution_id)
        return {"status": "completed", "execution_id": execution_id, **result}
    except Exception as e:
        log.error("taskiq.task.execution.failed", execution_id=execution_id, error=str(e))
        raise
