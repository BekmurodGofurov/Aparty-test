import uuid
from datetime import date
from typing import Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus

from database.operations.select import payments as select_payments


async def update_status(
    db: AsyncSession,
    payment_id: uuid.UUID,
    status: PaymentStatus,
) -> Optional[Payment]:
    await db.execute(update(Payment).where(Payment.id == payment_id).values(status=status))
    await db.commit()
    return await select_payments.get_by_id(db, payment_id)


async def mark_as_paid(db: AsyncSession, payment_id: uuid.UUID) -> Optional[Payment]:
    return await update_status(db, payment_id, PaymentStatus.paid)


async def mark_as_overdue(db: AsyncSession, payment_id: uuid.UUID) -> Optional[Payment]:
    return await update_status(db, payment_id, PaymentStatus.overdue)


async def update_fields(
    db: AsyncSession,
    payment_id: uuid.UUID,
    *,
    amount: int,
    billing_month: date,
    status: PaymentStatus,
) -> Optional[Payment]:
    await db.execute(
        update(Payment)
        .where(Payment.id == payment_id)
        .values(amount=amount, billing_month=billing_month, status=status)
    )
    await db.commit()
    return await select_payments.get_by_id(db, payment_id)
