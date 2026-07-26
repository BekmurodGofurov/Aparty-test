"""Users domain — Pydantic validation schemas.

All request/response models for auth, user profiles, and notifications.
These schemas MUST NOT import SQLAlchemy models from any other domain.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domains.users.models import NotificationType, UserRole


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """Sent by the Telegram bot after the user completes the FSM registration flow."""

    id: int = Field(..., gt=0, description="Telegram user ID — becomes the primary key")
    full_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    role: UserRole = UserRole.student


class CodeLoginRequest(BaseModel):
    """Sent by the React frontend with the 6-digit code obtained from the bot."""

    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class AdminLoginRequest(BaseModel):
    """Root admin login using environment credentials."""

    username: str
    password: str


class BotLoginCodeRequest(BaseModel):
    """Sent by the bot when the user types /login."""

    id: int = Field(..., description="Telegram user ID")


class BotLoginCodeResponse(BaseModel):
    code: str


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    success: bool = True
    message: str = "Token created successfully"
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class AuthSuccessResponse(BaseModel):
    success: bool = True
    message: str = "Authentication successful"
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# User profile schemas
# ---------------------------------------------------------------------------


class UserOut(BaseModel):
    id: int
    full_name: str
    phone: str
    role: UserRole
    university: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_verified: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    university: Optional[str] = None
    profile_picture_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    id: int = Field(gt=0)
    full_name: str
    phone: str
    role: UserRole
    university: Optional[str] = None
    profile_picture_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Notification schemas
# ---------------------------------------------------------------------------


class NotificationOut(BaseModel):
    id: uuid.UUID
    user_id: int
    actor_id: Optional[int] = None
    type: NotificationType
    title: str
    body: Optional[str] = None
    request_id: Optional[uuid.UUID] = None
    listing_id: Optional[uuid.UUID] = None
    target_url: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListOut(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int
