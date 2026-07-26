from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.apartments.models import Favorite


async def delete(db: AsyncSession, favorite: Favorite) -> None:
    await db.delete(favorite)
    await db.commit()
