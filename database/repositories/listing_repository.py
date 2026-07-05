import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Listing, TargetGender, ListingSource
from database.repositories.base_repository import BaseRepository


class ListingRepository(BaseRepository[Listing]):
    """Listing database operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Listing)

    async def get_by_owner_id(self, owner_id: int, skip: int = 0, limit: int = 100) -> List[Listing]:
        """Get all listings by owner"""
        result = await self.session.execute(
            select(Listing)
            .where(Listing.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_listings(
        self, skip: int = 0, limit: int = 100
    ) -> List[Listing]:
        """Get all active listings"""
        result = await self.session.execute(
            select(Listing)
            .where(Listing.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_region(
        self, region: str, skip: int = 0, limit: int = 100
    ) -> List[Listing]:
        """Get listings by region"""
        result = await self.session.execute(
            select(Listing)
            .where(and_(Listing.region == region, Listing.is_active == True))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_gender(
        self, gender: TargetGender, skip: int = 0, limit: int = 100
    ) -> List[Listing]:
        """Get listings by target gender"""
        result = await self.session.execute(
            select(Listing)
            .where(and_(Listing.target_gender == gender, Listing.is_active == True))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_premium_listings(
        self, skip: int = 0, limit: int = 100
    ) -> List[Listing]:
        """Get all premium listings that haven't expired"""
        result = await self.session.execute(
            select(Listing)
            .where(
                and_(
                    Listing.is_premium == True,
                    Listing.premium_expires_at > datetime.utcnow(),
                    Listing.is_active == True,
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def increment_view_count(self, listing_id: uuid.UUID) -> Optional[Listing]:
        """Increment view count for a listing"""
        listing = await self.get_by_id(listing_id)
        if listing:
            listing.view_count += 1
            await self.session.commit()
            await self.session.refresh(listing)
        return listing

    async def search(
        self,
        region: Optional[str] = None,
        district: Optional[str] = None,
        target_gender: Optional[TargetGender] = None,
        max_price: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Listing]:
        """Search listings with filters"""
        query = select(Listing).where(Listing.is_active == True)

        if region:
            query = query.where(Listing.region == region)
        if district:
            query = query.where(Listing.district == district)
        if target_gender:
            query = query.where(Listing.target_gender == target_gender)
        if max_price:
            query = query.where(Listing.price_usd <= max_price)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
