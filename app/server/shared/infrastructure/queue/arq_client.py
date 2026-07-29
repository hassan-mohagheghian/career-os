"""Server-side ARQ client for enqueuing background jobs.

Provides async helper functions to enqueue work to the ARQ/Redis queue.
The Background worker application picks up and processes these jobs.
"""

import asyncio
import os

from arq import create_pool
from arq.connections import RedisSettings


REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")


def _redis_settings() -> RedisSettings:
    return RedisSettings(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD or None,
    )


async def get_arq_pool():
    return await create_pool(_redis_settings())


async def close_arq_pool():
    pass


async def enqueue_process_job(job_id: int):
    pool = await get_arq_pool()
    try:
        await pool.enqueue_job("process_job", job_id)
    finally:
        await pool.aclose(close_connection_pool=True)


async def enqueue_process_company(company_id: int):
    pool = await get_arq_pool()
    try:
        await pool.enqueue_job("process_company", company_id)
    finally:
        await pool.aclose(close_connection_pool=True)


async def enqueue_process_generation(gen_id: int):
    pool = await get_arq_pool()
    try:
        await pool.enqueue_job("process_generation", gen_id)
    finally:
        await pool.aclose(close_connection_pool=True)


def enqueue_job_sync(job_id: int):
    asyncio.run(enqueue_process_job(job_id))


def enqueue_company_sync(company_id: int):
    asyncio.run(enqueue_process_company(company_id))


def enqueue_generation_sync(gen_id: int):
    asyncio.run(enqueue_process_generation(gen_id))
