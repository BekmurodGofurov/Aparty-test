import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


async def delete_by_id(db: AsyncSession, payment_id: uuid.UUID) -> bool:
    result = await db.execute(delete(Payment).where(Payment.id == payment_id))
    await db.commit()
    return result.rowcount > 0
