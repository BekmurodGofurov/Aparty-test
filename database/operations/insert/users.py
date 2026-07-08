from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def create(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
