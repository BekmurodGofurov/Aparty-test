from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ListingPaymentType(str, enum.Enum):
    regular = "regular"
    premium = "premium"


class ListingPaymentStatus(str, enum.Enum):
    paid = "paid"
    pending = "pending"


class ListingPayment(Base):
    __tablename__ = "listing_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[ListingPaymentType] = mapped_column(Enum(ListingPaymentType, name="listing_payment_type"), nullable=False)
    status: Mapped[ListingPaymentStatus] = mapped_column(Enum(ListingPaymentStatus, name="listing_payment_status"), default=ListingPaymentStatus.pending, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
