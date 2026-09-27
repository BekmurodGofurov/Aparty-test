"""Catalog Service Favorites Router (`/api/v1/favorites`): listings a user saved."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants import ALL_ROLES, API_PREFIX
from app.database import get_db
from app.mappers import listing_to_card
from app.models import Favorite, Listing, ListingStatus
from app.routers.listings import owner_profiles
from app.schemas import FavoriteStatus, FavoriteToggleResponse, ListingCard
from app.security import CurrentUser, get_current_user_id, require_roles

router = APIRouter(prefix=f"{API_PREFIX}/favorites", tags=["Favorites"])


@router.get("/me", response_model=list[ListingCard])
async def get_my_favorites(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Saved listings, most recently saved first. Deleted listings are left out."""
    stmt = (
        select(Listing)
        .join(Favorite, Favorite.listing_id == Listing.id)
        .options(selectinload(Listing.images))
        .where(Favorite.user_id == user_id, Listing.status != ListingStatus.deleted)
        .order_by(Favorite.created_at.desc())
    )
    listings = (await db.execute(stmt)).scalars().unique().all()
    profiles = await owner_profiles(listings)
    return [listing_to_card(item, profiles.get(item.owner_id), is_favorite=True) for item in listings]


@router.post("/{listing_id}", response_model=FavoriteToggleResponse)
async def toggle_favorite(
    listing_id: uuid.UUID,
    user: CurrentUser = Depends(require_roles(*ALL_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> FavoriteToggleResponse:
    """Save the listing, or remove it when it is already saved."""
    removed = await db.execute(
        delete(Favorite).where(Favorite.user_id == user.id, Favorite.listing_id == listing_id).returning(Favorite.listing_id)
    )
    if removed.first():
        await db.commit()
        return FavoriteToggleResponse(status=FavoriteStatus.removed)

    exists = await db.execute(
        select(Listing.id).where(Listing.id == listing_id, Listing.status != ListingStatus.deleted)
    )
    if exists.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")

    # A double click can race with itself; the composite key keeps a single row.
    await db.execute(insert(Favorite).values(user_id=user.id, listing_id=listing_id).on_conflict_do_nothing())
    await db.commit()
    return FavoriteToggleResponse(status=FavoriteStatus.added)
