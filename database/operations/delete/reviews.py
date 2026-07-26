from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.orders.models import Review


async def delete(db: AsyncSession, review: Review) -> None:
    await db.delete(review)
    await db.commit()
