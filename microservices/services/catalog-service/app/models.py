"""Catalog Service ORM models (`listings`, `listing_images`)."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import DEFAULT_LATITUDE, DEFAULT_LONGITUDE
from app.database import Base


class ListingStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    rented = "rented"
    deleted = "deleted"


class ListingTargetGender(str, enum.Enum):
    male = "male"
    female = "female"
    mixed = "mixed"


class ListingSource(str, enum.Enum):
    owner = "owner"
    makler = "makler"
    exiting_student = "exiting_student"
    roommate = "roommate"


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
    region: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    building_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, default=DEFAULT_LATITUDE, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, default=DEFAULT_LONGITUDE, nullable=False)
    rooms_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    area_m2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_gender: Mapped[ListingTargetGender] = mapped_column(
        SQLEnum(ListingTargetGender, name="listing_target_gender", create_constraint=False),
        default=ListingTargetGender.mixed,
        nullable=False,
        index=True,
    )
    source: Mapped[ListingSource] = mapped_column(
        SQLEnum(ListingSource, name="listing_source", create_constraint=False),
        default=ListingSource.owner,
        nullable=False,
    )
    max_guests: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_spaces: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    amenities: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    premium_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Roommate ads only: the apartment they belong to, who lives there now, and when the ad stops showing.
    parent_listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    residents_male: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    residents_female: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    residents_children: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    available_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    images: Mapped[List[ListingImage]] = relationship(
        "ListingImage", back_populates="listing", cascade="all, delete-orphan", lazy="selectin"
    )


    def __repr__(self) -> str:
        return f"<Listing id={self.id} owner_id={self.owner_id} title={self.title} status={self.status}>"


class Favorite(Base):
    """A listing a user saved. The user lives in IAM, so it is referenced by id only."""

    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


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
