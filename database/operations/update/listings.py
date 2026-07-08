import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing

from database.operations.select import listings as select_listings


async def apply_fields(db: AsyncSession, listing: Listing, **fields: Any) -> Listing:
    for key, value in fields.items():
        setattr(listing, key, value)
    await db.commit()
    await db.refresh(listing)
    return listing


async def activate_basic(
    db: AsyncSession,
    listing_id: uuid.UUID,
) -> None:
    await db.execute(
        update(Listing)
        .where(Listing.id == listing_id)
        .values(is_active=True, is_premium=False, premium_expires_at=None)
    )


async def upgrade_to_premium(
    db: AsyncSession,
    listing_id: uuid.UUID,
    premium_expires_at: datetime,
) -> None:
    await db.execute(
        update(Listing)
        .where(Listing.id == listing_id)
        .values(is_premium=True, is_active=True, premium_expires_at=premium_expires_at)
    )


async def mark_occupied(db: AsyncSession, listing: Listing) -> Listing:
    listing.available_spaces = 0
    listing.is_active = False
    await db.commit()
    await db.refresh(listing)
    return listing


async def mark_available(db: AsyncSession, listing: Listing) -> Listing:
    listing.available_spaces = max(1, listing.max_guests)
    listing.is_active = True
    await db.commit()
    await db.refresh(listing)
    return listing


async def increment_view_count(db: AsyncSession, listing_id: uuid.UUID) -> Optional[Listing]:
    listing = await select_listings.get_by_id(db, listing_id)
    if listing is None:
        return None
    listing.views_count += 1
    await db.commit()
    await db.refresh(listing)
    return listing


async def set_active_status(db: AsyncSession, listing: Listing, *, is_active: bool) -> Listing:
    listing.is_active = is_active
    await db.commit()
    await db.refresh(listing)
    return listing


async def decrement_available_spaces(db: AsyncSession, listing: Listing) -> Listing:
    listing.available_spaces = max(0, listing.available_spaces - 1)
    if listing.available_spaces == 0:
        listing.is_active = False
    return listing


async def increment_available_spaces(db: AsyncSession, listing: Listing) -> Listing:
    listing.available_spaces = min(listing.max_guests, listing.available_spaces + 1)
    listing.is_active = True
    return listing
