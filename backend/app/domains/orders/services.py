"""Orders domain — Core business logic (Actor-Command ready).

Contains:
  - premium_expiry_loop : Background task that expires overdue premium listings

RULE: This file MUST NOT import SQLAlchemy models from any other domain.
The Listing model is accessed via apartments domain's service layer when
a cross-domain read is required. The premium expiry DOES write to the
listings table — this is allowed because it's operating on a shared DB
schema concern that is owned by the apartments domain (Listing.is_premium).
We use raw SQL binding here to keep the write contained and avoid importing
the Listing ORM class directly.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def expire_premium_listings() -> None:
    """Bulk-update expired premium listings to is_premium=False.

    Uses a raw SQL UPDATE to avoid importing the Listing model from the
    apartments domain — this is the correct isolation approach.
    """
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        await db.execute(
            text(
                "UPDATE listings SET is_premium = FALSE "
                "WHERE is_premium = TRUE "
                "  AND premium_expires_at IS NOT NULL "
                "  AND premium_expires_at < :now"
            ),
            {"now": now},
        )
        await db.commit()
        logger.debug("Premium expiry check complete at %s.", now.isoformat())


async def premium_expiry_loop() -> None:
    """Infinite loop that expires premium listings every hour.

    Started as an ``asyncio.create_task()`` from ``core/lifespan.py``.
    """
    logger.info("Premium expiry daemon started (check interval: 3600s).")
    while True:
        await expire_premium_listings()
        await asyncio.sleep(3600)
