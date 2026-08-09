"""IAM Service — Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import UserRole


# ── Request schemas ───────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """Sent by the Telegram bot after the user completes the FSM registration flow."""

    id: int = Field(..., gt=0, description="Telegram user ID — stored as the primary key")
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=7, max_length=20)
    role: UserRole = UserRole.student


class BotLoginCodeRequest(BaseModel):
    """Sent by the Telegram bot when the user issues /login."""

    id: int = Field(..., gt=0, description="Telegram user ID")


class CodeLoginRequest(BaseModel):
    """Sent by the React frontend with the 6-digit code obtained from the bot."""

    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


# ── Response schemas ──────────────────────────────────────────────────────────


class UserOut(BaseModel):
    """Public user profile returned after registration or profile fetch."""

    id: int
    full_name: str
    phone: str
    role: UserRole
    university: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_verified: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BotLoginCodeResponse(BaseModel):
    """Code returned to the bot so it can display it to the user."""

    code: str


class AuthSuccessResponse(BaseModel):
    """Returned on successful OTP verification (login)."""

    success: bool = True
    message: str = "Authentication successful"
    access_token: str
    token_type: str = "bearer"
