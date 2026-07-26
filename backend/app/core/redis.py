"""Redis connection pool factory.

A single pool is created once at startup via ``create_redis_pool()`` and
stored on ``app.state.redis``. All consumers retrieve it from there — no
module-level global singletons that complicate testing.

Usage (in lifespan):
    redis = await create_redis_pool(settings.redis_url)
    app.state.redis = redis

Usage (in a route or service):
    redis: Redis = request.app.state.redis
"""

from __future__ import annotations

from redis.asyncio import Redis


async def create_redis_pool(url: str) -> Redis:
    """Create and return a connected async Redis client backed by a pool.

    Args:
        url: Redis connection URL, e.g. ``redis://localhost:6379``.

    Returns:
        A live ``redis.asyncio.Redis`` instance.
    """
    return Redis.from_url(url, encoding="utf-8", decode_responses=False)
