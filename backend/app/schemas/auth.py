from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    """Sent by the Telegram bot after the user completes the FSM registration flow.

    The `id` field is the Telegram user ID and will be stored as the primary key.
    No password is required — authentication uses the login-code flow instead.
    """
    id: int = Field(..., description="Telegram user ID — becomes the primary key")
    full_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    role: UserRole = UserRole.student


class CodeLoginRequest(BaseModel):
    """Sent by the React frontend with the 6-digit code obtained from the bot."""
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class AdminLoginRequest(BaseModel):
    """Sent by the React frontend when logging into the admin portal using root credentials."""
    username: str
    password: str


class BotLoginCodeRequest(BaseModel):
    """Sent by the bot when the user types /login — asks the backend to generate a code."""
    id: int = Field(..., description="Telegram user ID")


class BotLoginCodeResponse(BaseModel):
    """Backend response to the bot containing the generated login code."""
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

