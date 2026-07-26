import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.models import Notification

from database.operations.select import notifications as select_notifications


async def mark_read(db: AsyncSession, notification: Notification) -> Notification:
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(Notification).where(Notification.user_id == user_id).values(is_read=True)
    )
    await db.commit()
