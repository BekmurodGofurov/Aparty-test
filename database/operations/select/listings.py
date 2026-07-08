from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing, ListingTargetGender
from app.models.rental import Rental
from app.models.review import Review
from app.models.user import User, UserRole


async def get_by_id(db: AsyncSession, listing_id: uuid.UUID) -> Optional[Listing]:
    return await db.get(Listing, listing_id)


async def get_with_owner(
    db: AsyncSession,
    listing_id: uuid.UUID,
) -> Optional[tuple[Listing, User]]:
    result = await db.execute(
        select(Listing, User)
        .join(User, Listing.owner_id == User.id)
        .where(Listing.id == listing_id)
    )
    row = result.one_or_none()
    return row if row is None else (row[0], row[1])


async def get_all(db: AsyncSession, *, order_by_created_desc: bool = True) -> list[Listing]:
    query = select(Listing)
    if order_by_created_desc:
        query = query.order_by(Listing.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_by_owner_id(
    db: AsyncSession,
    owner_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Listing]:
    result = await db.execute(
        select(Listing)
        .where(Listing.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_active_listings(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Listing]:
    result = await db.execute(
        select(Listing)
        .where(Listing.is_active.is_(True))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_by_region(
    db: AsyncSession,
    region: str,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Listing]:
    result = await db.execute(
        select(Listing)
        .where(and_(Listing.region == region, Listing.is_active.is_(True)))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_by_gender(
    db: AsyncSession,
    gender: ListingTargetGender,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Listing]:
    result = await db.execute(
        select(Listing)
        .where(and_(Listing.target_gender == gender, Listing.is_active.is_(True)))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_premium_listings(
    db: AsyncSession,
    now: datetime,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Listing]:
    result = await db.execute(
        select(Listing)
        .where(
            and_(
                Listing.is_premium.is_(True),
                Listing.premium_expires_at > now,
                Listing.is_active.is_(True),
            )
        )
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def count_active_simple(db: AsyncSession, owner_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count(Listing.id)).where(
                Listing.owner_id == owner_id,
                Listing.is_active.is_(True),
                Listing.is_premium.is_(False),
            )
        )
        or 0
    )


async def count_active_premium(db: AsyncSession, owner_id: uuid.UUID, now: datetime) -> int:
    return (
        await db.scalar(
            select(func.count(Listing.id)).where(
                Listing.owner_id == owner_id,
                Listing.is_active.is_(True),
                Listing.is_premium.is_(True),
                Listing.premium_expires_at.is_not(None),
                Listing.premium_expires_at > now,
            )
        )
        or 0
    )


async def count_all(db: AsyncSession) -> int:
    return (await db.execute(select(func.count(Listing.id)))).scalar_one()


async def has_rental_history(db: AsyncSession, listing_id: uuid.UUID) -> bool:
    rental_id = await db.scalar(select(Rental.id).where(Rental.listing_id == listing_id).limit(1))
    return rental_id is not None


async def search(
    db: AsyncSession,
    *,
    region: Optional[str] = None,
    district: Optional[str] = None,
    target_gender: Optional[str] = None,
    max_price: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Listing]:
    query = select(Listing).where(Listing.is_active.is_(True))
    if region:
        query = query.where(Listing.region == region)
    if district:
        query = query.where(Listing.district == district)
    if target_gender:
        query = query.where(Listing.target_gender == target_gender)
    if max_price:
        query = query.where(Listing.price_usd <= max_price)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def search_with_cards(
    db: AsyncSession,
    *,
    filters: list,
    page: int,
    limit: int,
    now: datetime,
) -> tuple[list[tuple], int, int]:
    review_stats = (
        select(
            Review.listing_id.label("listing_id"),
            func.avg(Review.rating).label("rating"),
            func.count(Review.id).label("reviews_count"),
        )
        .group_by(Review.listing_id)
        .subquery()
    )
    premium_sort = case(
        (
            and_(
                Listing.is_premium.is_(True),
                Listing.premium_expires_at.is_not(None),
                Listing.premium_expires_at > now,
            ),
            1,
        ),
        else_=0,
    )
    base_query = (
        select(
            Listing,
            User.role.label("owner_role"),
            User.full_name.label("owner_full_name"),
            User.phone.label("owner_phone"),
            User.is_verified.label("owner_verified"),
            review_stats.c.rating,
            func.coalesce(review_stats.c.reviews_count, 0).label("reviews_count"),
        )
        .join(User, Listing.owner_id == User.id)
        .outerjoin(review_stats, review_stats.c.listing_id == Listing.id)
        .where(and_(*filters))
    )
    total = await db.scalar(select(func.count()).select_from(base_query.subquery()))
    total = total or 0
    pages = max(1, math.ceil(total / limit)) if total else 1
    offset = (page - 1) * limit
    rows = await db.execute(
        base_query.order_by(desc(premium_sort), desc(Listing.created_at)).offset(offset).limit(limit)
    )
    return list(rows.all()), total, pages


async def get_my_listing_rows(
    db: AsyncSession,
    owner_id: uuid.UUID,
    *,
    page: int,
    limit: int,
) -> list[tuple]:
    review_stats = (
        select(
            Review.listing_id.label("listing_id"),
            func.avg(Review.rating).label("rating"),
            func.count(Review.id).label("reviews_count"),
        )
        .group_by(Review.listing_id)
        .subquery()
    )
    rows = await db.execute(
        select(
            Listing,
            User.role.label("owner_role"),
            User.full_name.label("owner_full_name"),
            User.phone.label("owner_phone"),
            User.is_verified.label("owner_verified"),
            review_stats.c.rating,
            func.coalesce(review_stats.c.reviews_count, 0).label("reviews_count"),
        )
        .join(User, Listing.owner_id == User.id)
        .outerjoin(review_stats, review_stats.c.listing_id == Listing.id)
        .where(Listing.owner_id == owner_id)
        .order_by(desc(Listing.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return list(rows.all())


async def get_owner_listings_with_review_counts(
    db: AsyncSession,
    owner_id: uuid.UUID,
) -> list[tuple[Listing, int]]:
    review_counts = (
        select(Review.listing_id, func.count(Review.id).label("reviews_count"))
        .group_by(Review.listing_id)
        .subquery()
    )
    rows = await db.execute(
        select(Listing, func.coalesce(review_counts.c.reviews_count, 0))
        .outerjoin(review_counts, review_counts.c.listing_id == Listing.id)
        .where(Listing.owner_id == owner_id)
        .order_by(Listing.created_at.desc())
    )
    return [(listing, int(reviews_count or 0)) for listing, reviews_count in rows.all()]
