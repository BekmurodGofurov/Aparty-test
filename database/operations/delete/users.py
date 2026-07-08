from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def delete(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()
