from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import Favorite


async def delete(db: AsyncSession, favorite: Favorite) -> None:
    await db.delete(favorite)
    await db.commit()
