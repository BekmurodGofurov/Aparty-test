"""Apartments domain — view-sync async write-behind daemon.

Architecture:
  - Writes go to Redis (fast, non-blocking) via ``increment_apartment_view()``.
  - Every 5 minutes, ``view_sync_daemon()`` wakes up and bulk-flushes counts
    from Redis into PostgreSQL using a single batched UPDATE — O(n) not O(n²).
  - The DIRTY SET pattern (SADD / SPOP) ensures we only touch rows that
    actually received views since the last flush cycle.

CRITICAL: This file MUST NOT import from any other domain's models.py.
It writes directly against the ``listings`` table via the apartment domain's
own Listing model.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Dict, List

from redis.asyncio import Redis
from sqlalchemy import bindparam, update

from app.core.database import AsyncSessionLocal
from app.domains.apartments.models import Listing

logger = logging.getLogger(__name__)

DIRTY_SET_KEY = "aparty:views:dirty"
VIEW_KEY_PREFIX = "aparty:views:"


async def increment_apartment_view(
    apartment_id: uuid.UUID, redis_client: Redis
) -> None:
    """Atomically increment the view count in Redis and mark the apartment dirty.

    Uses a pipeline (MULTI/EXEC) to guarantee both operations are atomic.

    Args:
        apartment_id: The UUID of the apartment that was viewed.
        redis_client: The shared Redis connection from ``app.state.redis``.
    """
    view_key = f"{VIEW_KEY_PREFIX}{str(apartment_id)}"
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.incr(view_key)
        pipe.sadd(DIRTY_SET_KEY, str(apartment_id))
        await pipe.execute()


async def sync_views_to_db(redis_client: Redis) -> None:
    """Flush dirty view counts from Redis to PostgreSQL in a single batch.

    Uses SPOP (atomic pop) so a concurrent flush cycle cannot double-count.
    On any exception, dirty IDs are re-added to Redis so no views are lost.
    """
    try:
        dirty_ids_bytes = await redis_client.spop(DIRTY_SET_KEY, 10_000)
        if not dirty_ids_bytes:
            return

        dirty_ids: List[str] = [
            apt_id.decode("utf-8") if isinstance(apt_id, bytes) else apt_id
            for apt_id in dirty_ids_bytes
        ]

        view_keys = [f"{VIEW_KEY_PREFIX}{apt_id}" for apt_id in dirty_ids]
        view_counts = await redis_client.mget(view_keys)

        update_params: List[Dict] = []
        keys_to_delete: List[str] = []

        for apt_id, count_bytes in zip(dirty_ids, view_counts):
            if count_bytes is None:
                continue
            count_str = (
                count_bytes.decode("utf-8")
                if isinstance(count_bytes, bytes)
                else count_bytes
            )
            update_params.append(
                {"b_id": uuid.UUID(apt_id), "b_views": int(count_str)}
            )
            keys_to_delete.append(f"{VIEW_KEY_PREFIX}{apt_id}")

        if not update_params:
            return

        async with AsyncSessionLocal() as session:
            async with session.begin():
                stmt = (
                    update(Listing)
                    .where(Listing.id == bindparam("b_id"))
                    .values(
                        views_count=Listing.views_count + bindparam("b_views")
                    )
                )
                await session.execute(stmt, update_params)

        if keys_to_delete:
            await redis_client.delete(*keys_to_delete)

        logger.info(
            "View sync: flushed %d apartments to DB.", len(update_params)
        )

    except Exception:
        logger.exception("View sync failed; re-queuing dirty IDs.")
        if dirty_ids_bytes:
            await redis_client.sadd(DIRTY_SET_KEY, *dirty_ids_bytes)


async def view_sync_daemon(redis_client: Redis) -> None:
    """Infinite loop that flushes views every 5 minutes.

    Designed to run as an ``asyncio.create_task()`` from ``core/lifespan.py``.
    """
    logger.info("View sync daemon started (flush interval: 300s).")
    while True:
        await asyncio.sleep(300)
        await sync_views_to_db(redis_client)
