from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review


async def delete(db: AsyncSession, review: Review) -> None:
    await db.delete(review)
    await db.commit()
