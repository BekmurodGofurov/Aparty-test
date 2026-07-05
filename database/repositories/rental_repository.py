import uuid
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rental
from database.repositories.base_repository import BaseRepository


class RentalRepository(BaseRepository[Rental]):
    """Rental database operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Rental)

    async def get_by_listing_id(
        self, listing_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Rental]:
        """Get all rentals for a listing"""
        result = await self.session.execute(
            select(Rental)
            .where(Rental.listing_id == listing_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_tenant_id(
        self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Rental]:
        """Get all rentals for a tenant"""
        result = await self.session.execute(
            select(Rental)
            .where(Rental.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_rentals(
        self, skip: int = 0, limit: int = 100
    ) -> List[Rental]:
        """Get all active rentals"""
        result = await self.session.execute(
            select(Rental)
            .where(Rental.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_listing_and_tenant(
        self, listing_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Optional[Rental]:
        """Get rental by listing and tenant"""
        result = await self.session.execute(
            select(Rental).where(
                and_(
                    Rental.listing_id == listing_id,
                    Rental.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def deactivate(self, rental_id: uuid.UUID) -> Optional[Rental]:
        """Mark rental as inactive"""
        return await self.update(rental_id, is_active=False)
