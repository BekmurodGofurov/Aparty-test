import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.favorite import Favorite
from app.models.listing import Listing
from app.models.review import Review
from app.models.user import User
from app.schemas.listing import ListingCard

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
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.listing_id == listing_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()
        return {"status": "removed"}
    
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing topilmadi")

    new_fav = Favorite(user_id=current_user.id, listing_id=listing_id)
    db.add(new_fav)
    await db.commit()
    return {"status": "added"}

@router.get("/me", response_model=List[ListingCard])
async def get_my_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    
    result = await db.execute(
        select(
            Listing,
            User.role.label("owner_role"),
            User.full_name.label("owner_name"),
            User.is_verified.label("owner_verified"),
            func.avg(Review.rating).label("rating"),
            func.count(Review.id).label("review_count")
        )
        .join(User, User.id == Listing.owner_id)
        .join(Favorite, Favorite.listing_id == Listing.id)
        .outerjoin(Review, Review.listing_id == Listing.id)
        .where(Favorite.user_id == current_user.id)
        .group_by(Listing.id, User.id)
        .order_by(desc(Listing.created_at))
    )
    
    cards: list[ListingCard] = []
    for listing, owner_role, owner_name, owner_verified, rating, review_count in result.all():
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
