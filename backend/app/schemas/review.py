from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserMin(BaseModel):
    id: int
    full_name: str
    profile_picture_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    listing_id: uuid.UUID
    rating: Optional[int] = Field(default=0, ge=0, le=5)
    review_text: Optional[str] = None


class ReviewOut(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    author_id: int
    rating: Optional[int] = None
    review_text: Optional[str] = None
    created_at: datetime
    author: Optional[UserMin] = None

    model_config = ConfigDict(from_attributes=True)
