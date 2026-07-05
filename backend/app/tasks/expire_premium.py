from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import update

from app.database import AsyncSessionLocal
from app.models.listing import Listing


async def expire_premium_listings() -> None:
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        await db.execute(
            update(Listing)
            .where(Listing.is_premium.is_(True))
            .where(Listing.premium_expires_at.is_not(None))
            .where(Listing.premium_expires_at < now)
            .values(is_premium=False)
        )
        await db.commit()


async def premium_expiry_loop() -> None:
    while True:
        await expire_premium_listings()
        await asyncio.sleep(3600)
