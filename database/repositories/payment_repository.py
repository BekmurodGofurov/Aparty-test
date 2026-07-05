import uuid
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, PaymentStatus
from database.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Payment database operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Payment)

    async def get_by_rental_id(
        self, rental_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        """Get all payments for a rental"""
        result = await self.session.execute(
            select(Payment)
            .where(Payment.rental_id == rental_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_payer_id(
        self, payer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        """Get all payments by a payer"""
        result = await self.session.execute(
            select(Payment)
            .where(Payment.payer_id == payer_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_status(
        self, status: PaymentStatus, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        """Get payments by status"""
        result = await self.session.execute(
            select(Payment)
            .where(Payment.status == status)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_pending_payments(
        self, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        """Get all pending payments"""
        return await self.get_by_status(PaymentStatus.pending, skip, limit)

    async def get_overdue_payments(
        self, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        """Get all overdue payments"""
        return await self.get_by_status(PaymentStatus.overdue, skip, limit)

    async def mark_as_paid(self, payment_id: uuid.UUID) -> Optional[Payment]:
        """Mark payment as paid"""
        return await self.update(payment_id, status=PaymentStatus.paid)

    async def mark_as_overdue(self, payment_id: uuid.UUID) -> Optional[Payment]:
        """Mark payment as overdue"""
        return await self.update(payment_id, status=PaymentStatus.overdue)

    async def get_by_rental_and_month(
        self, rental_id: uuid.UUID, month: str
    ) -> Optional[Payment]:
        """Get payment for a specific rental and month"""
        result = await self.session.execute(
            select(Payment).where(
                and_(
                    Payment.rental_id == rental_id,
                    Payment.month == month,
                )
            )
        )
        return result.scalar_one_or_none()
