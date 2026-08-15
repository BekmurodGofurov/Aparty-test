"""Catalog Service ORM models (`listings`, `listing_images`, and `bookings`)."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum as SQLEnum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ListingStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    rented = "rented"
    deleted = "deleted"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    rejected = "rejected"


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[int] = mapped_column(
        BigInteger, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[ListingStatus] = mapped_column(
        SQLEnum(ListingStatus, name="listing_status", create_constraint=False),
        default=ListingStatus.active,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    images: Mapped[List[ListingImage]] = relationship(
        "ListingImage", back_populates="listing", cascade="all, delete-orphan", lazy="selectin"
    )
    bookings: Mapped[List[Booking]] = relationship(
        "Booking", back_populates="listing", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Listing id={self.id} owner_id={self.owner_id} title={self.title} status={self.status}>"


class ListingImage(Base):
    __tablename__ = "listing_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    delete_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    listing: Mapped[Listing] = relationship("Listing", back_populates="images")

    def __repr__(self) -> str:
        return f"<ListingImage id={self.id} listing_id={self.listing_id} is_primary={self.is_primary}>"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, name="booking_status", create_constraint=False),
        default=BookingStatus.pending,
        nullable=False,
        index=True,
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    listing: Mapped[Listing] = relationship("Listing", back_populates="bookings")

    def __repr__(self) -> str:
        return f"<Booking id={self.id} listing_id={self.listing_id} user_id={self.user_id} status={self.status}>"
