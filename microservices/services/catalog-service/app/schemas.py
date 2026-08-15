"""Catalog Service Pydantic DTO Schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models import BookingStatus, ListingStatus


# ── Media Upload Schemas ──────────────────────────────────────────────────────
class ImageUploadResponse(BaseModel):
    display_url: str = Field(..., description="Uploaded image CDN/display URL")
    delete_url: Optional[str] = Field(None, description="Image deletion URL")
    provider: str = Field("imgbb", description="Image storage provider name")


# ── Listing Schemas ───────────────────────────────────────────────────────────
class ListingImageCreate(BaseModel):
    image_url: str = Field(..., description="ImgBB/Media CDN image URL")
    delete_url: Optional[str] = Field(None, description="Optional image deletion URL")
    is_primary: bool = Field(False, description="Flag indicating primary cover image")


class ListingImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing_id: uuid.UUID
    image_url: str
    delete_url: Optional[str] = None
    is_primary: bool


class ListingCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    property_type: str = Field(..., min_length=2, max_length=50)
    images: List[ListingImageCreate] = Field(default_factory=list)


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    property_type: Optional[str] = Field(None, min_length=2, max_length=50)
    status: Optional[ListingStatus] = None
    images: Optional[List[ListingImageCreate]] = None


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: int
    title: str
    description: Optional[str] = None
    price: float
    property_type: str
    status: ListingStatus
    images: List[ListingImageOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# ── Booking Schemas ───────────────────────────────────────────────────────────
class BookingCreate(BaseModel):
    listing_id: uuid.UUID = Field(..., description="Target listing UUID to book")
    start_date: date = Field(..., description="Booking start date")
    end_date: date = Field(..., description="Booking end date")
    message: Optional[str] = Field(None, description="Optional note for the listing owner")


class BookingStatusUpdate(BaseModel):
    status: BookingStatus = Field(..., description="New status for the booking (confirmed/cancelled/rejected)")


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing_id: uuid.UUID
    user_id: int
    start_date: date
    end_date: date
    total_price: float
    status: BookingStatus
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
