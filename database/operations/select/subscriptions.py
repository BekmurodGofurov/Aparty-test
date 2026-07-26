import uuid
from datetime import date
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.orders.models import Subscription, SubscriptionType


async def get_by_id(db: AsyncSession, subscription_id: uuid.UUID) -> Optional[Subscription]:
    result = await db.execute(select(Subscription).where(Subscription.id == subscription_id))
    return result.scalar_one_or_none()


async def get_by_user_id(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Subscription]:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_my_subscriptions(db: AsyncSession, user_id: uuid.UUID) -> list[Subscription]:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
    )
    return list(result.scalars().all())


async def get_active_subscription(db: AsyncSession, user_id: uuid.UUID, today: date) -> Optional[Subscription]:
    return await db.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.is_active.is_(True),
            Subscription.start_date <= today,
            Subscription.end_date >= today,
            Subscription.used_count < Subscription.listing_limit,
        )
        .order_by(Subscription.created_at.desc())
    )


async def get_by_type(
    db: AsyncSession,
    sub_type: SubscriptionType,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Subscription]:
    result = await db.execute(
        select(Subscription).where(Subscription.type == sub_type).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def has_available_listings(db: AsyncSession, subscription_id: uuid.UUID) -> bool:
    sub = await get_by_id(db, subscription_id)
    if sub is None:
        return False
    return sub.used_count < sub.listing_limit
