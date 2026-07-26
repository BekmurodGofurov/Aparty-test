import uuid
from datetime import date
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.orders.models import Payment, PaymentStatus


async def get_by_id(db: AsyncSession, payment_id: uuid.UUID) -> Optional[Payment]:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()


async def get_by_rental_id(
    db: AsyncSession,
    rental_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Payment]:
    result = await db.execute(
        select(Payment).where(Payment.rental_id == rental_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_by_payer_id(
    db: AsyncSession,
    payer_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Payment]:
    result = await db.execute(
        select(Payment).where(Payment.payer_id == payer_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def list_by_payer(
    db: AsyncSession,
    payer_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 10,
) -> list[Payment]:
    result = await db.execute(
        select(Payment).where(Payment.payer_id == payer_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_by_status(
    db: AsyncSession,
    status: PaymentStatus,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Payment]:
    result = await db.execute(
        select(Payment).where(Payment.status == status).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_pending_payments(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Payment]:
    return await get_by_status(db, PaymentStatus.pending, skip=skip, limit=limit)


async def get_overdue_payments(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Payment]:
    return await get_by_status(db, PaymentStatus.overdue, skip=skip, limit=limit)


async def get_by_rental_and_month(
    db: AsyncSession,
    rental_id: uuid.UUID,
    billing_month: date,
) -> Optional[Payment]:
    result = await db.execute(
        select(Payment).where(
            and_(Payment.rental_id == rental_id, Payment.billing_month == billing_month)
        )
    )
    return result.scalar_one_or_none()


async def sum_total_revenue(db: AsyncSession) -> float:
    revenue = (await db.execute(select(func.coalesce(func.sum(Payment.amount), 0)))).scalar_one()
    return float(revenue or 0)
