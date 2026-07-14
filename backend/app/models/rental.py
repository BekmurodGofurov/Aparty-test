from __future__ import annotations

import uuid
import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    price_usd: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    listing = relationship("Listing", back_populates="rentals")
    student = relationship("User", back_populates="rentals")
    payments = relationship("Payment", back_populates="rental")
    room_messages = relationship("RoomMessage", back_populates="rental")
    maintenance_reports = relationship("MaintenanceReport", back_populates="rental")


class RentalRequest(Base):
    __tablename__ = "rental_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[RentalRequestStatus] = mapped_column(Enum(RentalRequestStatus, name="rental_request_status"), default=RentalRequestStatus.pending, nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rental_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("rentals.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    listing = relationship("Listing")
    requester = relationship("User", foreign_keys=[requester_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    rental = relationship("Rental")
    messages = relationship("RentalRequestMessage", back_populates="request")


class RentalRequestMessage(Base):
    __tablename__ = "rental_request_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rental_requests.id"), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request = relationship("RentalRequest", back_populates="messages")
    sender = relationship("User")


class RoomMessage(Base):
    __tablename__ = "room_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rental_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rentals.id"), nullable=False)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    rental = relationship("Rental", back_populates="room_messages")
    listing = relationship("Listing")
    sender = relationship("User")


class MaintenanceReport(Base):
    __tablename__ = "maintenance_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rental_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rentals.id"), nullable=False)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    reporter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[MaintenanceReportStatus] = mapped_column(Enum(MaintenanceReportStatus, name="maintenance_report_status"), default=MaintenanceReportStatus.open, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    rental = relationship("Rental", back_populates="maintenance_reports")
    listing = relationship("Listing")
    reporter = relationship("User", foreign_keys=[reporter_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
