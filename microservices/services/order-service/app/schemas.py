"""Order Service Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import BookingStatus


class BookingCreate(BaseModel):
    listing_id: uuid.UUID
    start_date: date
    end_date: date
    message: Optional[str] = Field(None, max_length=1000)


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class PublicProfile(BaseModel):
    id: int
    full_name: str
    phone: Optional[str] = None
    is_verified: bool = False


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing_id: uuid.UUID
    apartment_listing_id: uuid.UUID
    is_roommate_request: bool
    listing_owner_id: int
    listing_title: Optional[str] = None
    user_id: int
    requester: Optional[PublicProfile] = None
    start_date: date
    end_date: date
    total_price: float
    status: BookingStatus
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ListingBookingInfo(BaseModel):
    """Listing data returned by the Catalog Service booking-info endpoint."""

    id: uuid.UUID
    owner_id: int
    title: str = ""
    price: float
    status: str
    is_active: bool
    rental_type: str
    available_spaces: int = 1
    parent_listing_id: Optional[uuid.UUID] = None
