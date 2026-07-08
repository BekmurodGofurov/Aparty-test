from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


async def create(db: AsyncSession, payment: Payment) -> Payment:
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment
