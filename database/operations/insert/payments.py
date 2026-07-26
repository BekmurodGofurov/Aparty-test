from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.orders.models import Payment


async def create(db: AsyncSession, payment: Payment) -> Payment:
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment
