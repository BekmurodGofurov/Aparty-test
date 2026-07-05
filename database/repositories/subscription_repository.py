import uuid
from typing import Optional, List
from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subscription, SubscriptionType
from database.repositories.base_repository import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    """Subscription database operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Subscription)

    async def get_by_user_id(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Subscription]:
        """Get all subscriptions for a user"""
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_subscription(
        self, user_id: uuid.UUID
    ) -> Optional[Subscription]:
        """Get active subscription for a user"""
        today = date.today()
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.is_active == True,
                    Subscription.start_date <= today,
                    Subscription.end_date >= today,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_type(
        self, sub_type: SubscriptionType, skip: int = 0, limit: int = 100
    ) -> List[Subscription]:
        """Get subscriptions by type"""
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.type == sub_type)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def deactivate(self, subscription_id: uuid.UUID) -> Optional[Subscription]:
        """Deactivate subscription"""
        return await self.update(subscription_id, is_active=False)

    async def increment_used_count(
        self, subscription_id: uuid.UUID
    ) -> Optional[Subscription]:
        """Increment used listings count"""
        sub = await self.get_by_id(subscription_id)
        if sub:
            sub.used_count += 1
            await self.session.commit()
            await self.session.refresh(sub)
        return sub

    async def has_available_listings(
        self, subscription_id: uuid.UUID
    ) -> bool:
        """Check if subscription has available listings"""
        sub = await self.get_by_id(subscription_id)
        if sub:
            return sub.used_count < sub.listings_limit
        return False
