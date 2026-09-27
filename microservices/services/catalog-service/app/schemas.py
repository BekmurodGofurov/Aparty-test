"""Catalog Service Pydantic schemas."""

from __future__ import annotations

import uuid
import enum
from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.constants import DEFAULT_LATITUDE, DEFAULT_LONGITUDE, MAX_RESIDENTS_PER_GROUP, MAX_ROOMMATE_SPACES
from app.models import ListingSource, ListingStatus, ListingTargetGender


class ImageUploadResponse(BaseModel):
    url: str = Field(..., description="Compatibility URL used by the current frontend")
    display_url: str = Field(..., description="Uploaded image CDN/display URL")
    delete_url: Optional[str] = Field(None, description="Image deletion URL")
    provider: str = Field("imgbb", description="Image storage provider name")


# ── Listing Schemas ───────────────────────────────────────────────────────────
class RentalType(str, enum.Enum):
    full_unit = "full_unit"
    shared_room = "shared_room"


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
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    region: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    building_number: Optional[str] = Field(None, max_length=20)
    room_number: Optional[str] = Field(None, max_length=20)
    floor: Optional[int] = Field(None, ge=0)
    total_floors: Optional[int] = Field(None, ge=1)
    latitude: float = DEFAULT_LATITUDE
    longitude: float = DEFAULT_LONGITUDE
    rooms_count: int = Field(1, ge=1)
    area_m2: Optional[int] = Field(None, ge=1)
    target_gender: ListingTargetGender = ListingTargetGender.mixed
    rental_type: RentalType = RentalType.full_unit
    max_guests: int = Field(1, ge=1)
    available_spaces: int = Field(1, ge=0)
    amenities: dict = Field(default_factory=dict)
    images: List[Any] = Field(default_factory=list)
    is_premium: bool = False
    is_active: Optional[bool] = None


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    status: Optional[ListingStatus] = None
    region: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    building_number: Optional[str] = Field(None, max_length=20)
    room_number: Optional[str] = Field(None, max_length=20)
    floor: Optional[int] = Field(None, ge=0)
    total_floors: Optional[int] = Field(None, ge=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rooms_count: Optional[int] = Field(None, ge=1)
    area_m2: Optional[int] = Field(None, ge=1)
    target_gender: Optional[ListingTargetGender] = None
    rental_type: Optional[RentalType] = None
    max_guests: Optional[int] = Field(None, ge=1)
    available_spaces: Optional[int] = Field(None, ge=0)
    amenities: Optional[dict] = None
    images: Optional[List[Any]] = None
    residents_male: Optional[int] = Field(None, ge=0, le=MAX_RESIDENTS_PER_GROUP)
    residents_female: Optional[int] = Field(None, ge=0, le=MAX_RESIDENTS_PER_GROUP)
    residents_children: Optional[int] = Field(None, ge=0, le=MAX_RESIDENTS_PER_GROUP)
    available_from: Optional[date] = None
    is_premium: Optional[bool] = None
    premium_expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class ListingOut(BaseModel):
    id: uuid.UUID
    owner_id: int
    title: str
    description: Optional[str] = None
    price: float
    rental_type: RentalType
    status: ListingStatus
    region: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    building_number: Optional[str] = None
    room_number: Optional[str] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    latitude: float = DEFAULT_LATITUDE
    longitude: float = DEFAULT_LONGITUDE
    rooms_count: int = 1
    area_m2: Optional[int] = None
    target_gender: ListingTargetGender = ListingTargetGender.mixed
    source: ListingSource = ListingSource.owner
    max_guests: int = 1
    available_spaces: int = 1
    amenities: dict = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    is_premium: bool = False
    premium_expires_at: Optional[datetime] = None
    is_active: bool = True
    views_count: int = 0
    parent_listing_id: Optional[uuid.UUID] = None
    residents_male: Optional[int] = None
    residents_female: Optional[int] = None
    residents_children: Optional[int] = None
    available_from: Optional[date] = None
    expires_at: Optional[datetime] = None
    owner_full_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_telegram_url: Optional[str] = None
    owner_role: Optional[str] = None
    owner_verified: bool = False
    rating: Optional[float] = None
    reviews_count: int = 0
    is_favorite: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListingCard(BaseModel):
    id: uuid.UUID
    owner_id: int
    title: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    latitude: float = DEFAULT_LATITUDE
    longitude: float = DEFAULT_LONGITUDE
    rooms_count: int = 1
    area_m2: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    price: float
    rental_type: RentalType
    target_gender: ListingTargetGender = ListingTargetGender.mixed
    available_spaces: int = 1
    max_guests: int = 1
    amenities: dict = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    is_premium: bool = False
    is_active: bool = True
    views_count: int = 0
    premium_expires_at: Optional[datetime] = None
    parent_listing_id: Optional[uuid.UUID] = None
    residents_male: Optional[int] = None
    residents_female: Optional[int] = None
    residents_children: Optional[int] = None
    available_from: Optional[date] = None
    expires_at: Optional[datetime] = None
    owner_role: str = "owner"
    owner_full_name: str = ""
    owner_phone: Optional[str] = None
    owner_telegram_url: Optional[str] = None
    owner_verified: bool = False
    rating: Optional[float] = None
    reviews_count: int = 0
    is_favorite: bool = False
    created_at: datetime


class ListingSearchResponse(BaseModel):
    success: bool = True
    message: str = "Listings retrieved successfully"
    listings: List[ListingCard]
    total: int
    page: int
    pages: int


class FavoriteStatus(str, enum.Enum):
    added = "added"
    removed = "removed"


class FavoriteToggleResponse(BaseModel):
    status: FavoriteStatus


class ActivateListingResponse(BaseModel):
    success: bool = True
    message: str = "Listing activated"


class UpgradeToPremiumResponse(BaseModel):
    success: bool = True
    message: str = "Listing upgraded to premium"
    premium_expires_at: datetime


class ListingBookingInfo(BaseModel):
    """Minimal listing data the Order Service needs to create a booking."""

    id: uuid.UUID
    owner_id: int
    title: str
    price: float
    status: ListingStatus
    is_active: bool
    rental_type: RentalType
    available_spaces: int
    parent_listing_id: Optional[uuid.UUID] = None


class RoommateListingCreate(BaseModel):
    """A tenant looks for roommates. Location and photos come from the apartment."""

    residents_male: int = Field(0, ge=0, le=MAX_RESIDENTS_PER_GROUP)
    residents_female: int = Field(0, ge=0, le=MAX_RESIDENTS_PER_GROUP)
    residents_children: int = Field(0, ge=0, le=MAX_RESIDENTS_PER_GROUP)
    available_spaces: int = Field(1, ge=1, le=MAX_ROOMMATE_SPACES)
    target_gender: ListingTargetGender = ListingTargetGender.mixed
    available_from: Optional[date] = Field(None, description="First day a newcomer can move in. Empty means anytime.")
    price: float = Field(..., gt=0)
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    amenities: Optional[dict] = None
