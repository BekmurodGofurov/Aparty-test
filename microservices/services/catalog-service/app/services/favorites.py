"""Saved-listing lookups shared by the routers."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Favorite


async def favorite_listing_ids(db: AsyncSession, user_id: Optional[int], listing_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    """Which of `listing_ids` the user saved. Anonymous users have none."""
    if user_id is None or not listing_ids:
        return set()
    result = await db.execute(
        select(Favorite.listing_id).where(Favorite.user_id == user_id, Favorite.listing_id.in_(listing_ids))
    )
    return set(result.scalars())
