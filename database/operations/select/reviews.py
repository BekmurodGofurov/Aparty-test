import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review
from app.models.user import User


async def get_by_id(db: AsyncSession, review_id: uuid.UUID) -> Optional[Review]:
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()


async def get_by_listing_id(
    db: AsyncSession,
    listing_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Review]:
    result = await db.execute(
        select(Review).where(Review.listing_id == listing_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_by_listing_with_author(db: AsyncSession, listing_id: uuid.UUID) -> list[Review]:
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.author))
        .where(Review.listing_id == listing_id)
        .order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())


async def get_by_author_id(
    db: AsyncSession,
    author_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Review]:
    result = await db.execute(
        select(Review).where(Review.author_id == author_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_by_listing_and_author(
    db: AsyncSession,
    listing_id: uuid.UUID,
    author_id: uuid.UUID,
) -> Optional[Review]:
    return await db.scalar(
        select(Review).where(
            Review.listing_id == listing_id,
            Review.author_id == author_id,
        )
    )


async def get_average_rating(db: AsyncSession, listing_id: uuid.UUID) -> Optional[float]:
    result = await db.execute(
        select(func.avg(Review.rating)).where(Review.listing_id == listing_id)
    )
    avg = result.scalar()
    return float(avg) if avg else None


async def count_by_listing(db: AsyncSession, listing_id: uuid.UUID) -> int:
    return (
        await db.scalar(select(func.count(Review.id)).where(Review.listing_id == listing_id))
        or 0
    )


async def get_listing_reviews_with_authors(
    db: AsyncSession,
    listing_id: uuid.UUID,
) -> list[tuple[Review, User]]:
    result = await db.execute(
        select(Review, User)
        .join(User, User.id == Review.author_id)
        .where(Review.listing_id == listing_id)
        .order_by(Review.created_at.desc())
    )
    return list(result.all())


async def get_with_author(db: AsyncSession, review_id: uuid.UUID) -> Optional[Review]:
    return await db.scalar(
        select(Review).options(selectinload(Review.author)).where(Review.id == review_id)
    )
