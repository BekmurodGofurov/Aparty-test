"""Application lifespan manager.

Centralises all startup/shutdown side effects so that main.py stays a pure
entrypoint with zero business logic.

Startup sequence (order matters):
  1. Run DB migrations (sync, in a thread pool executor).
  2. Initialise Redis pool — stored on app.state.redis.
  3. Initialise FastAPICache with the Redis backend.
  4. Initialise RabbitMQ connection and setup publisher.
  5. Register domain event subscribers (cross-domain wiring).
  6. Start background daemons:
       a. Premium-expiry loop  (domains.orders)
       b. View-sync daemon      (domains.apartments)
       c. RabbitMQ message consumer

Shutdown sequence (LIFO):
  1. Cancel all background daemon tasks.
  2. Close Redis and RabbitMQ connections gracefully.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.core.config import settings
from app.core.redis import create_redis_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 1. Database migrations ─────────────────────────────────────────────
    from app.core.db_migrations import run_migrations

    logger.info("Running database migrations...")
    await asyncio.to_thread(run_migrations)
    logger.info("Migrations complete.")

    # ── 2. Redis pool ──────────────────────────────────────────────────────
    redis = await create_redis_pool(settings.redis_url)
    app.state.redis = redis
    FastAPICache.init(RedisBackend(redis), prefix="aparty-cache")
    logger.info("Redis pool initialised at %s.", settings.redis_url)

    # ── 3. RabbitMQ Connection ─────────────────────────────────────────────
    from app.core.rabbitmq import create_rabbitmq_connection
    from app.core.events import setup_publisher, start_message_consumer

    rabbitmq = await create_rabbitmq_connection(settings.rabbitmq_url)
    app.state.rabbitmq = rabbitmq
    await setup_publisher(rabbitmq)
    logger.info("RabbitMQ connection initialised at %s.", settings.rabbitmq_url)

    # ── 4. Register event subscribers (cross-domain wiring) ────────────────
    # Imported here to avoid circular imports at module load time.
    # These calls are side-effect registrations, not function calls.
    from app.domains.users import register_event_handlers as _reg_users  # noqa: F401
    from app.domains.apartments import register_event_handlers as _reg_apartments  # noqa: F401

    _reg_users()
    _reg_apartments()

    # ── 5. Background daemons ──────────────────────────────────────────────
    from app.domains.orders.services import premium_expiry_loop
    from app.domains.apartments.view_sync import view_sync_daemon

    premium_task = asyncio.create_task(premium_expiry_loop(), name="premium-expiry")
    view_sync_task = asyncio.create_task(view_sync_daemon(redis), name="view-sync-daemon")
    rabbitmq_consumer_task = asyncio.create_task(start_message_consumer(rabbitmq), name="rabbitmq-consumer")
    
    logger.info("Background daemons started: [premium-expiry, view-sync-daemon, rabbitmq-consumer].")

    try:
        yield  # ← Application runs here
    finally:
        # ── Shutdown ───────────────────────────────────────────────────────
        logger.info("Shutting down background daemons...")
        premium_task.cancel()
        view_sync_task.cancel()
        rabbitmq_consumer_task.cancel()
        await asyncio.gather(premium_task, view_sync_task, rabbitmq_consumer_task, return_exceptions=True)

        logger.info("Closing Redis connection...")
        await redis.aclose()
        
        logger.info("Closing RabbitMQ connection...")
        await rabbitmq.close()
        
        logger.info("Lifespan shutdown complete.")
