from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.apartments.models import Favorite


async def create(db: AsyncSession, favorite: Favorite) -> Favorite:
    db.add(favorite)
    await db.commit()
    return favorite
