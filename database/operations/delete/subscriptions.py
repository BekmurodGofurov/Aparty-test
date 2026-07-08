import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from database.operations.select import subscriptions as select_subscriptions


async def delete_by_id(db: AsyncSession, subscription_id: uuid.UUID) -> bool:
    sub = await select_subscriptions.get_by_id(db, subscription_id)
    if sub is None:
        return False
    await db.delete(sub)
    await db.commit()
    return True
