"""IAM Service — Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import UserRole


class TelegramLoginStartResponse(BaseModel):
    authorization_url: str


class TelegramCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=2048)
    state: str = Field(..., min_length=1, max_length=256)


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class SelectableRole(str, Enum):
    student = "student"
    owner = "owner"
    makler = "makler"


class RoleSelectRequest(BaseModel):
    role: SelectableRole


class UserUpdate(BaseModel):
    """Profile fields a user may edit. The phone number comes from Telegram and cannot be changed.

    English field names are canonical. Uzbek aliases are accepted because the
    current React profile screens submit those keys.
    """

    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    university: Optional[str] = Field(None, max_length=100)
    profile_picture_url: Optional[str] = None
    ism: Optional[str] = Field(None, min_length=2, max_length=100)
    universitet: Optional[str] = Field(None, max_length=100)
    rasm_url: Optional[str] = None


# ── Response schemas ──────────────────────────────────────────────────────────


class UserOut(BaseModel):
    id: int
    full_name: str
    phone: str
    role: Optional[UserRole] = None
    university: Optional[str] = None
    profile_picture_url: Optional[str] = None
    telegram_username: Optional[str] = None
    is_verified: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PublicProfileOut(BaseModel):
    """Contact-safe user data shown next to listings. Served to internal services only."""

    id: int
    full_name: str
    phone: Optional[str] = None
    telegram_username: Optional[str] = None
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class AuthSuccessResponse(BaseModel):
    success: bool = True
    access_token: str
    token_type: str = "bearer"
    needs_role: bool = False
    user: Optional[UserOut] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
