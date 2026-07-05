from __future__ import annotations

import uuid
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.listing import ListingSource, ListingTargetGender


class ListingBase(BaseModel):
    region: str
    district: str
    address: Optional[str] = None
    building_number: Optional[str] = None
    room_number: Optional[str] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    latitude: float = 41.311081
    longitude: float = 69.240562
    rooms_count: int = Field(ge=1)
    area_m2: Optional[int] = Field(default=None, ge=1)
    price_usd: int = Field(ge=1)
    target_gender: ListingTargetGender = ListingTargetGender.mixed
    source: ListingSource = ListingSource.owner
    max_guests: int = Field(default=1, ge=1)
    available_spaces: int = Field(default=1, ge=0)
    amenities: dict = Field(default_factory=dict)
    images: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    is_premium: bool = False

    model_config = ConfigDict(from_attributes=True)


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    region: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    building_number: Optional[str] = None
    room_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rooms_count: Optional[int] = Field(default=None, ge=1)
    floor: Optional[int] = Field(default=None, ge=0)
    total_floors: Optional[int] = Field(default=None, ge=1)
    target_gender: Optional[ListingTargetGender] = None
    max_guests: Optional[int] = Field(default=None, ge=1)
    amenities: Optional[dict] = None
    images: Optional[list[str]] = None
    price_usd: Optional[int] = Field(default=None, ge=1)
    available_spaces: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ListingOut(ListingBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    owner_full_name: Optional[str] = None
    owner_phone: Optional[str] = None
    premium_expires_at: Optional[datetime] = None
    is_active: bool
    views_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListingCard(BaseModel):
    id: uuid.UUID
    region: str
    district: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    rooms_count: int
    area_m2: Optional[int] = None
    floor: Optional[int] = None
    price_usd: int
    target_gender: ListingTargetGender
    available_spaces: int
    amenities: dict
    images: list[str]
    description: Optional[str] = None
    is_premium: bool
    is_active: bool
    views_count: int = 0
    premium_expires_at: Optional[datetime] = None
    owner_role: str
    owner_full_name: str
    owner_phone: Optional[str] = None
    owner_verified: bool
    rating: Optional[float] = None
    reviews_count: int = 0
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ListingSearchResponse(BaseModel):
    success: bool = True
    message: str = "Listings retrieved successfully"
    listings: list[ListingCard]
    total: int
    page: int
    pages: int


class UpgradeToPremiumResponse(BaseModel):
    success: bool = True
    message: str = "Listing upgraded to premium"
    premium_expires_at: datetime


class ActivateListingResponse(BaseModel):
    success: bool = True
    message: str = "Listing activated"
