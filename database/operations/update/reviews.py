import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.orders.models import Review

from database.operations.select import reviews as select_reviews


async def update_fields(db: AsyncSession, review: Review, **fields) -> Review:
    for key, value in fields.items():
        setattr(review, key, value)
    await db.commit()
    await db.refresh(review)
    return review
