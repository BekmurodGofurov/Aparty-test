from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription


async def create(db: AsyncSession, subscription: Subscription) -> Subscription:
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription
