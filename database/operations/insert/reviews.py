from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review


async def create(db: AsyncSession, review: Review) -> Review:
    db.add(review)
    await db.commit()
    await db.refresh(review)
    created = await db.scalar(
        select(Review).options(selectinload(Review.author)).where(Review.id == review.id)
    )
    return created or review
