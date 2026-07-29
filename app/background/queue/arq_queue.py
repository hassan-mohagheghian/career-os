"""ARQ queue configuration and helper functions."""

from arq import create_pool
from arq.connections import RedisSettings
from arq.worker import Worker as ArqWorker

from background.config.settings import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    QUEUE_NAME,
    WORKER_CONCURRENCY,
    WORKER_POLL_INTERVAL,
)
from background.workers.job_worker import process_job as arq_process_job
from background.workers.company_worker import process_company as arq_process_company
from background.workers.generation_worker import process_generation as arq_process_generation


def redis_settings() -> RedisSettings:
    return RedisSettings(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD or None,
    )


FUNCTIONS = [
    arq_process_job,
    arq_process_company,
    arq_process_generation,
]


async def create_arq_pool():
    return await create_pool(redis_settings())


async def enqueue_job(arq_pool, job_id: int, _job_type: str = "job"):
    await arq_pool.enqueue_job("process_job", job_id)


async def enqueue_company(arq_pool, company_id: int):
    await arq_pool.enqueue_job("process_company", company_id)


async def enqueue_generation(arq_pool, gen_id: int):
    await arq_pool.enqueue_job("process_generation", gen_id)
