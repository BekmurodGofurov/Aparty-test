"""
High-performance cache manager with TTL + Jitter anti-stampede logic.

Jitter Explained
~~~~~~~~~~~~~~~~
When many cache entries share the same TTL, they expire simultaneously,
causing a **cache stampede** — thousands of requests hit the database at once.
By adding a random jitter to each TTL::

    effective_ttl = base_ttl + random.uniform(-jitter, +jitter)

entries expire at staggered intervals, spreading the database load evenly.
"""

from __future__ import annotations

import functools
import json
import logging
import random
import uuid
from datetime import datetime
from typing import Any, Callable, TypeVar

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# JSON serialisation helpers
# ---------------------------------------------------------------------------


class _CacheEncoder(json.JSONEncoder):
    """Custom JSON encoder for uuid.UUID, datetime, and Pydantic models."""

    def default(self, o: Any) -> Any:  # noqa: ANN401
        if isinstance(o, uuid.UUID):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, BaseModel):
            return o.model_dump(mode="json")
        return super().default(o)


def _serialize(value: Any) -> str:  # noqa: ANN401
    return json.dumps(value, cls=_CacheEncoder)


def _deserialize(raw: str | bytes) -> Any:  # noqa: ANN401
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


# ---------------------------------------------------------------------------
# CacheManager
# ---------------------------------------------------------------------------


class CacheManager:
    """Thin async wrapper around a ``redis.asyncio.Redis`` connection."""

    __slots__ = ("_redis",)

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> Any | None:  # noqa: ANN401
        """Return the cached value for *key*, or ``None`` on a miss."""
        try:
            raw: bytes | None = await self._redis.get(key)
        except RedisError:
            logger.warning("Redis GET failed for key=%s", key, exc_info=True)
            return None

        if raw is None:
            return None

        try:
            return _deserialize(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Cache deserialisation failed for key=%s", key, exc_info=True)
            return None

    async def set(
        self,
        key: str,
        value: Any,  # noqa: ANN401
        ttl: int = 300,
        jitter_range: int = 60,
    ) -> None:
        """Store *value* under *key* with a jittered TTL."""
        effective_ttl = max(1, int(ttl + random.uniform(-jitter_range, jitter_range)))
        serialized = _serialize(value)
        try:
            await self._redis.setex(key, effective_ttl, serialized)
        except RedisError:
            logger.warning("Redis SETEX failed for key=%s", key, exc_info=True)

    async def delete(self, key: str) -> None:
        """Remove a single key from the cache."""
        try:
            await self._redis.delete(key)
        except RedisError:
            logger.warning("Redis DELETE failed for key=%s", key, exc_info=True)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching *pattern* using ``SCAN`` (never ``KEYS``)."""
        deleted = 0
        try:
            cursor: int | bytes = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor=cursor, match=pattern, count=100,
                )
                if keys:
                    await self._redis.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
        except RedisError:
            logger.warning(
                "Redis SCAN/DELETE failed for pattern=%s", pattern, exc_info=True,
            )
        return deleted


# ---------------------------------------------------------------------------
# @cached() decorator
# ---------------------------------------------------------------------------


def cached(
    key_template: str,
    ttl: int = 300,
    jitter_range: int = 60,
) -> Callable[[F], F]:
    """Decorator that adds transparent Redis caching to an async FastAPI endpoint."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            request: Request | None = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request is None:
                return await func(*args, **kwargs)

            try:
                redis_conn: Redis = request.app.state.redis
            except AttributeError:
                return await func(*args, **kwargs)

            cache = CacheManager(redis_conn)
            cache_key = key_template
            try:
                cache_key = key_template.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                pass

            if request.query_params:
                sorted_qs = "&".join(
                    f"{k}={v}" for k, v in sorted(request.query_params.items())
                )
                cache_key = f"{cache_key}:{sorted_qs}"

            try:
                cached_data = await cache.get(cache_key)
            except Exception:  # noqa: BLE001
                cached_data = None

            if cached_data is not None:
                return JSONResponse(content=cached_data, headers={"X-Cache": "HIT"})

            result = await func(*args, **kwargs)

            response_body: Any
            if isinstance(result, JSONResponse):
                response_body = json.loads(result.body)
            elif isinstance(result, BaseModel):
                response_body = result.model_dump(mode="json")
            elif isinstance(result, dict):
                response_body = result
            else:
                response_body = result

            try:
                await cache.set(cache_key, response_body, ttl=ttl, jitter_range=jitter_range)
            except Exception:  # noqa: BLE001
                logger.warning("Failed to write cache for key=%s", cache_key, exc_info=True)

            return JSONResponse(content=response_body, headers={"X-Cache": "MISS"})

        return wrapper  # type: ignore[return-value]

    return decorator  # type: ignore[return-value]
