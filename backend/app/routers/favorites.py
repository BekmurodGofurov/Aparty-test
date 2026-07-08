import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.favorite import Favorite
from app.models.user import User
from app.schemas.listing import ListingCard
from database.operations.delete import favorites as delete_favorites
from database.operations.insert import favorites as insert_favorites
from database.operations.select import favorites as select_favorites
from database.operations.select import listings as select_listings

router = APIRouter()


def _is_premium_active(is_premium: bool, premium_expires_at, now: datetime) -> bool:
    if not is_premium or premium_expires_at is None:
        return False
    if premium_expires_at.tzinfo is None:
        premium_expires_at = premium_expires_at.replace(tzinfo=timezone.utc)
    return premium_expires_at > now


@router.post("/{listing_id}", status_code=status.HTTP_201_CREATED)
async def toggle_favorite(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await select_favorites.get_by_user_and_listing(db, current_user.id, listing_id)

    if existing:
        await delete_favorites.delete(db, existing)
        return {"status": "removed"}

    listing = await select_listings.get_by_id(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing topilmadi")

    await insert_favorites.create(db, Favorite(user_id=current_user.id, listing_id=listing_id))
    return {"status": "added"}


@router.get("/me", response_model=List[ListingCard])
async def get_my_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    rows = await select_favorites.get_my_favorites_rows(db, current_user.id)

    cards: list[ListingCard] = []
    for listing, owner_role, owner_name, owner_verified, rating, review_count in rows:
        cards.append(
            ListingCard(
                id=listing.id,
                region=listing.region,
                district=listing.district,
                address=listing.address,
                latitude=listing.latitude,
                longitude=listing.longitude,
                rooms_count=listing.rooms_count,
                area_m2=listing.area_m2,
                floor=listing.floor,
                price_usd=listing.price_usd,
                target_gender=listing.target_gender,
                available_spaces=listing.available_spaces,
                amenities=listing.amenities or {},
                images=listing.images[:1] if listing.images else [],
                description=listing.description,
                is_premium=_is_premium_active(listing.is_premium, listing.premium_expires_at, now),
                is_active=listing.is_active,
                views_count=listing.views_count,
                premium_expires_at=listing.premium_expires_at,
                owner_role=owner_role.value if owner_role else "student",
                owner_full_name=owner_name or "",
                owner_verified=bool(owner_verified),
                rating=round(float(rating), 1) if rating is not None else None,
                reviews_count=int(review_count or 0),
                created_at=listing.created_at,
            )
        )
    return cards
