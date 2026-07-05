import uuid
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Review
from database.repositories.base_repository import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    """Review database operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Review)

    async def get_by_listing_id(
        self, listing_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        """Get all reviews for a listing"""
        result = await self.session.execute(
            select(Review)
            .where(Review.listing_id == listing_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_author_id(
        self, author_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        """Get all reviews by an author"""
        result = await self.session.execute(
            select(Review)
            .where(Review.author_id == author_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_listing_and_author(
        self, listing_id: uuid.UUID, author_id: uuid.UUID
    ) -> Optional[Review]:
        """Get review by listing and author"""
        result = await self.session.execute(
            select(Review).where(
                Review.listing_id == listing_id,
                Review.author_id == author_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_average_rating(self, listing_id: uuid.UUID) -> Optional[float]:
        """Get average rating for a listing"""
        result = await self.session.execute(
            select(func.avg(Review.rating)).where(Review.listing_id == listing_id)
        )
        avg = result.scalar()
        return float(avg) if avg else None
