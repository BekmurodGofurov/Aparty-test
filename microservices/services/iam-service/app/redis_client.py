"""IAM Service — Redis async client.

Key conventions:
  otp:{user_id}    → 6-digit code (TTL = OTP_TTL_SECONDS)
  otp_code:{code}  → user_id      (TTL = OTP_TTL_SECONDS)

Two keys are stored per OTP so that the /auth/login endpoint can perform
a reverse lookup (code → user_id) without scanning the entire keyspace.
Both keys are deleted atomically after a successful login.
"""

from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level client; initialised in app lifespan.
_redis: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """Create the Redis connection pool.  Called once on application startup."""
    global _redis
    _redis = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    # Validate connectivity immediately
    await _redis.ping()
    logger.info("Redis connection established: %s", settings.redis_url)


async def close_redis() -> None:
    """Close the Redis connection pool.  Called on application shutdown."""
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
        logger.info("Redis connection closed.")


def get_redis() -> aioredis.Redis:
    """Return the active Redis client (raises if not yet initialised)."""
    if _redis is None:
        raise RuntimeError("Redis is not initialised. Call init_redis() first.")
    return _redis


# ── OTP helpers ───────────────────────────────────────────────────────────────


async def save_otp(user_id: int, code: str) -> None:
    """Store two Redis keys that represent a single OTP token.

    otp:{user_id}  → code   (forward lookup  — verify the code for a user)
    otp_code:{code} → user_id (reverse lookup — find user_id from a bare code)

    Both keys share the same TTL so they expire together.
    """
    r = get_redis()
    ttl = settings.otp_ttl_seconds
    async with r.pipeline(transaction=True) as pipe:
        pipe.set(f"otp:{user_id}", code, ex=ttl)
        pipe.set(f"otp_code:{code}", str(user_id), ex=ttl)
        await pipe.execute()


async def get_user_id_by_code(code: str) -> Optional[int]:
    """Reverse-lookup: return the user_id bound to *code*, or None if expired/absent."""
    r = get_redis()
    raw = await r.get(f"otp_code:{code}")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


async def verify_and_consume_otp(code: str) -> Optional[int]:
    """Validate the OTP and return the bound user_id, then delete both keys atomically.

    Returns None if the code does not exist or has expired.
    """
    r = get_redis()
    user_id = await get_user_id_by_code(code)
    if user_id is None:
        return None

    # Delete both keys atomically with a pipeline
    async with r.pipeline(transaction=True) as pipe:
        pipe.delete(f"otp_code:{code}")
        pipe.delete(f"otp:{user_id}")
        await pipe.execute()

    return user_id
