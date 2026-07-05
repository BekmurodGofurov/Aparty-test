from __future__ import annotations

import uuid
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class UserOut(BaseModel):
    id: uuid.UUID
    full_name: str
    phone: str
    email: Optional[str] = None
    role: UserRole
    university: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    university: Optional[str] = None
    profile_picture_url: Optional[str] = None
    password: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    role: UserRole
    university: Optional[str] = None
    profile_picture_url: Optional[str] = None
    password: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
