"""Pydantic v2 response schemas for the apartments API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PopularApartmentItem(BaseModel):
    """Schema representing a single popular apartment listing."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    region: str
    district: str
    address: Optional[str] = None
    rooms_count: int
    area_m2: Optional[int] = None
    price_usd: int
    images: list[str] = []
    is_premium: bool = False
    views_count: int = 0
    created_at: datetime


class PopularApartmentsResponse(BaseModel):
    """Envelope schema for the popular apartments endpoint."""

    apartments: list[PopularApartmentItem]
    total: int
    cached: bool
