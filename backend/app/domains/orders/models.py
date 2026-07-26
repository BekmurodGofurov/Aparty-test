"""Orders domain — SQLAlchemy ORM models.

Contains:
  - Rental, RentalRequest, RentalRequestMessage, RentalRequestStatus
  - RoomMessage, MaintenanceReport, MaintenanceReportStatus
  - Payment, PaymentStatus
  - Review
  - Subscription, SubscriptionType
  - ListingPayment, ListingPaymentType, ListingPaymentStatus

RULE: This file MUST ONLY import from ``app.core.database`` (for Base).
      It must NEVER import from any other domain's models.py.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Rental
# ---------------------------------------------------------------------------


class RentalRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class MaintenanceReportStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"


class Rental(Base):
    __tablename__ = "rentals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    price_usd: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    listing = relationship("Listing", back_populates="rentals")
    student = relationship("User", back_populates="rentals")
    payments = relationship("Payment", back_populates="rental")
    room_messages = relationship("RoomMessage", back_populates="rental")
    maintenance_reports = relationship("MaintenanceReport", back_populates="rental")


class RentalRequest(Base):
    __tablename__ = "rental_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False
    )
    requester_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[RentalRequestStatus] = mapped_column(
        Enum(RentalRequestStatus, name="rental_request_status"),
        default=RentalRequestStatus.pending,
        nullable=False,
        index=True,
    )
    message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rental_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rentals.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    listing = relationship("Listing")
    requester = relationship("User", foreign_keys=[requester_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    rental = relationship("Rental")
    messages = relationship("RentalRequestMessage", back_populates="request")


class RentalRequestMessage(Base):
    __tablename__ = "rental_request_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rental_requests.id"), nullable=False
    )
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    request = relationship("RentalRequest", back_populates="messages")
    sender = relationship("User")


class RoomMessage(Base):
    __tablename__ = "room_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rental_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rentals.id"), nullable=False
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False
    )
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    rental = relationship("Rental", back_populates="room_messages")
    listing = relationship("Listing")
    sender = relationship("User")


class MaintenanceReport(Base):
    __tablename__ = "maintenance_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rental_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rentals.id"), nullable=False
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False
    )
    reporter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    recipient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[MaintenanceReportStatus] = mapped_column(
        Enum(MaintenanceReportStatus, name="maintenance_report_status"),
        default=MaintenanceReportStatus.open,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    rental = relationship("Rental", back_populates="maintenance_reports")
    listing = relationship("Listing")
    reporter = relationship("User", foreign_keys=[reporter_id])
    recipient = relationship("User", foreign_keys=[recipient_id])


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------


class PaymentStatus(str, enum.Enum):
    paid = "paid"
    pending = "pending"
    overdue = "overdue"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rental_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rentals.id", ondelete="CASCADE"), nullable=False
    )
    payer_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_month: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.pending,
        nullable=False,
        index=True,
    )
    payment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    rental = relationship("Rental", back_populates="payments")
    payer = relationship("User")


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("listing_id", "author_id", name="uq_listing_author"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    listing = relationship("Listing", back_populates="reviews")
    author = relationship("User", back_populates="reviews")


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------


class SubscriptionType(str, enum.Enum):
    owner_monthly = "owner_monthly"
    makler_s = "makler_s"
    makler_l = "makler_l"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType, name="subscription_type"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    listing_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="subscriptions")


# ---------------------------------------------------------------------------
# ListingPayment (financial transaction for listing activation/premium)
# ---------------------------------------------------------------------------


class ListingPaymentType(str, enum.Enum):
    regular = "regular"
    premium = "premium"


class ListingPaymentStatus(str, enum.Enum):
    paid = "paid"
    pending = "pending"


class ListingPayment(Base):
    __tablename__ = "listing_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[ListingPaymentType] = mapped_column(
        Enum(ListingPaymentType, name="listing_payment_type"), nullable=False
    )
    status: Mapped[ListingPaymentStatus] = mapped_column(
        Enum(ListingPaymentStatus, name="listing_payment_status"),
        default=ListingPaymentStatus.pending,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
