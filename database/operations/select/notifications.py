import uuid
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def get_by_id(db: AsyncSession, notification_id: uuid.UUID) -> Optional[Notification]:
    return await db.get(Notification, notification_id)


async def get_my_notifications(db: AsyncSession, user_id: uuid.UUID, *, limit: int = 30) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def count_unread(db: AsyncSession, user_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        or 0
    )
