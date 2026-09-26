"""Redis connection used for login state, refresh sessions and rate limits."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlsplit

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    global _redis
    _redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    await _redis.ping()
    logger.info("Redis connection established: %s", urlsplit(settings.redis_url).hostname)


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis is not initialised. Call init_redis() first.")
    return _redis
