"""Apartments domain — SQLAlchemy ORM models.

Contains:
  - Listing, ListingTargetGender, ListingSource  (from app/models/listing.py)
  - Favorite                                     (from app/models/favorite.py)

RULE: This file MUST ONLY import from ``app.core.database`` (for Base).
      It must NEVER import from any other domain's models.py.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Listing enums
# ---------------------------------------------------------------------------


class ListingTargetGender(str, enum.Enum):
    male = "male"
    female = "female"
    mixed = "mixed"


class ListingSource(str, enum.Enum):
    owner = "owner"
    makler = "makler"
    exiting_student = "exiting_student"


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
        nullable=False,
    )
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    building_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    rooms_count: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    area_m2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    price_usd: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_gender: Mapped[ListingTargetGender] = mapped_column(
        Enum(ListingTargetGender, name="listing_target_gender"),
        nullable=False,
        index=True,
    )
    source: Mapped[ListingSource] = mapped_column(
        Enum(ListingSource, name="listing_source"), nullable=False
    )
    max_guests: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_spaces: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    amenities: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    images: Mapped[list[str]] = mapped_column(
        ARRAY(String()), nullable=False, default=list
    )
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_premium: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    premium_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # String-based relationships to avoid cross-domain model imports (Removed for strict database isolation)
    # owner = relationship("User", back_populates="listings")
    # rentals = relationship("Rental", back_populates="listing")
    # reviews = relationship("Review", back_populates="listing")


# ---------------------------------------------------------------------------
# Favorite
# ---------------------------------------------------------------------------


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", name="_user_listing_favorite_uc"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
        nullable=False,
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Removed for strict database isolation
    # user = relationship("User")
    listing = relationship("Listing")
