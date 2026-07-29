"""Redis connection configuration for ARQ."""

from redis.asyncio import ConnectionPool, Redis

from .settings import REDIS_URL


_pool: ConnectionPool | None = None


def create_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(REDIS_URL)
    return _pool


async def create_redis() -> Redis:
    pool = create_pool()
    return Redis(connection_pool=pool)


async def close_redis():
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
