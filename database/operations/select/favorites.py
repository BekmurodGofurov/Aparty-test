import uuid
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.apartments.models import Favorite
from app.domains.apartments.models import Listing
from app.domains.orders.models import Review
from app.domains.users.models import User


async def get_by_user_and_listing(
    db: AsyncSession,
    user_id: uuid.UUID,
    listing_id: uuid.UUID,
) -> Optional[Favorite]:
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.listing_id == listing_id)
    )
    return result.scalar_one_or_none()


async def get_my_favorites_rows(db: AsyncSession, user_id: uuid.UUID) -> list[tuple]:
    result = await db.execute(
        select(
            Listing,
            User.role.label("owner_role"),
            User.full_name.label("owner_name"),
            User.is_verified.label("owner_verified"),
            func.avg(Review.rating).label("rating"),
            func.count(Review.id).label("review_count"),
        )
        .join(User, User.id == Listing.owner_id)
        .join(Favorite, Favorite.listing_id == Listing.id)
        .outerjoin(Review, Review.listing_id == Listing.id)
        .where(Favorite.user_id == user_id)
        .group_by(Listing.id, User.id)
        .order_by(desc(Listing.created_at))
    )
    return list(result.all())
