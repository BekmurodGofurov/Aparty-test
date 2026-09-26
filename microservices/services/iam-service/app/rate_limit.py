"""Fixed-window counters in Redis."""

from __future__ import annotations

from fastapi import HTTPException, Request

from app.redis_client import get_redis

TOO_MANY_REQUESTS = 429


def client_ip(request: Request) -> str:
    """Client address as set by the gateway (X-Real-IP), falling back to the socket peer."""
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")


async def enforce_rate_limit(scope: str, identity: str, limit: int, window_seconds: int) -> None:
    """Count one hit and raise 429 once `limit` hits were made in the window."""
    key = f"ratelimit:{scope}:{identity}"
    redis = get_redis()
    hits = await redis.incr(key)
    if hits == 1:
        await redis.expire(key, window_seconds)
    if hits > limit:
        raise HTTPException(status_code=TOO_MANY_REQUESTS, detail="Too many requests. Try again later.")


async def is_locked(scope: str, identity: str, limit: int) -> bool:
    raw = await get_redis().get(f"ratelimit:{scope}:{identity}")
    return raw is not None and int(raw) >= limit


async def record_failure(scope: str, identity: str, window_seconds: int) -> None:
    key = f"ratelimit:{scope}:{identity}"
    redis = get_redis()
    if await redis.incr(key) == 1:
        await redis.expire(key, window_seconds)


async def clear(scope: str, identity: str) -> None:
    await get_redis().delete(f"ratelimit:{scope}:{identity}")
