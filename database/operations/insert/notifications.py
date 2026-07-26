from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.models import Notification


async def create(db: AsyncSession, notification: Notification) -> Notification:
    db.add(notification)
    return notification
