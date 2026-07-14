from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PaymentStatus(str, enum.Enum):
    paid = "paid"
    pending = "pending"
    overdue = "overdue"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rental_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rentals.id", ondelete="CASCADE"), nullable=False)
    payer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_month: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.pending, nullable=False, index=True)
    payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    # Relationships
    rental = relationship("Rental", back_populates="payments")
    payer = relationship("User")
