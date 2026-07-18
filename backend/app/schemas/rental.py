from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.rental import MaintenanceReportStatus, RentalRequestStatus


class RentalCreate(BaseModel):
    listing_id: uuid.UUID
    student_id: int
    start_date: date
    end_date: Optional[date] = None
    price_usd: int = Field(ge=1)


class RentalOut(BaseModel):
    id: uuid.UUID
    listing_id: Optional[uuid.UUID] = None
    student_id: int
    start_date: date
    end_date: Optional[date] = None
    price_usd: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OwnerRentalStudent(BaseModel):
    id: int
    full_name: str
    phone: str
    is_verified: bool
    
    model_config = ConfigDict(from_attributes=True)


class OwnerRentalListing(BaseModel):
    id: uuid.UUID
    region: str
    district: str
    address: Optional[str] = None
    price_usd: int
    
    model_config = ConfigDict(from_attributes=True)


class OwnerRentalOut(BaseModel):
    id: uuid.UUID
    listing_id: Optional[uuid.UUID] = None
    student: OwnerRentalStudent
    listing: Optional[OwnerRentalListing] = None
    start_date: date
    end_date: Optional[date] = None
    price_usd: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RentalRequestCreate(BaseModel):
    listing_id: uuid.UUID
    message: Optional[str] = Field(default=None, max_length=1000)


class RentalMessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class RentalRequestUser(BaseModel):
    id: int
    full_name: str
    phone: str
    is_verified: bool
    
    model_config = ConfigDict(from_attributes=True)


class RentalRequestListing(BaseModel):
    id: uuid.UUID
    region: str
    district: str
    address: Optional[str] = None
    price_usd: int
    images: list[str] = []
    
    model_config = ConfigDict(from_attributes=True)


class RentalRequestOut(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    requester: RentalRequestUser
    recipient: RentalRequestUser
    listing: RentalRequestListing
    status: RentalRequestStatus
    message: Optional[str] = None
    rental_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RentalRequestMessageOut(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    sender_id: int
    sender_name: str
    text: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RoomListingOut(BaseModel):
    id: uuid.UUID
    region: str
    district: str
    address: Optional[str] = None
    room_number: Optional[str] = None
    price_usd: int
    images: list[str] = []
    available_spaces: int
    max_guests: int
    
    model_config = ConfigDict(from_attributes=True)


class RoomNeighborOut(BaseModel):
    id: int
    full_name: str
    phone: str
    is_verified: bool
    
    model_config = ConfigDict(from_attributes=True)


class MyRoomOut(BaseModel):
    id: uuid.UUID
    listing_id: Optional[uuid.UUID] = None
    listing: Optional[RoomListingOut] = None
    owner: RentalRequestUser
    neighbors: list[RoomNeighborOut]
    start_date: date
    end_date: Optional[date] = None
    price_usd: int
    is_active: bool
    next_payment_date: Optional[date] = None
    payment_days_left: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RoomMessageOut(BaseModel):
    id: uuid.UUID
    rental_id: uuid.UUID
    listing_id: uuid.UUID
    sender_id: int
    sender_name: str
    text: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MaintenanceReportCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    image_url: Optional[str] = Field(default=None, max_length=1000)


class MaintenanceReportOut(BaseModel):
    id: uuid.UUID
    rental_id: uuid.UUID
    listing_id: uuid.UUID
    reporter_id: int
    recipient_id: int
    text: str
    image_url: Optional[str] = None
    status: MaintenanceReportStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VacancyRepostCreate(BaseModel):
    available_spaces: int = Field(ge=1, le=2)
    description: Optional[str] = Field(default=None, max_length=1000)
