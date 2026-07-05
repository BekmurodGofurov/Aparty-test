from __future__ import annotations

import enum
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Float, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ListingTargetGender(str, enum.Enum):
    male = "male"
    female = "female"
    mixed = "mixed"


class ListingSource(str, enum.Enum):
    owner = "owner"
    makler = "makler"
    exiting_student = "exiting_student"


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    building_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    rooms_count: Mapped[int] = mapped_column(Integer, nullable=False)
    area_m2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    price_usd: Mapped[int] = mapped_column(Integer, nullable=False)
    target_gender: Mapped[ListingTargetGender] = mapped_column(Enum(ListingTargetGender, name="listing_target_gender"), nullable=False)
    source: Mapped[ListingSource] = mapped_column(Enum(ListingSource, name="listing_source"), nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_spaces: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    amenities: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    images: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    premium_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="listings")
    rentals = relationship("Rental", back_populates="listing")
    reviews = relationship("Review", back_populates="listing")
