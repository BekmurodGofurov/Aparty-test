import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription

from database.operations.select import subscriptions as select_subscriptions


async def deactivate(db: AsyncSession, subscription_id: uuid.UUID) -> Optional[Subscription]:
    sub = await select_subscriptions.get_by_id(db, subscription_id)
    if sub is None:
        return None
    sub.is_active = False
    await db.commit()
    await db.refresh(sub)
    return sub


async def increment_used_count(db: AsyncSession, subscription_id: uuid.UUID) -> Optional[Subscription]:
    sub = await select_subscriptions.get_by_id(db, subscription_id)
    if sub is None:
        return None
    sub.used_count += 1
    await db.commit()
    await db.refresh(sub)
    return sub
