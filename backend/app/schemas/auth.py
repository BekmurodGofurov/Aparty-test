from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    email: Optional[str] = None
    university: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6, max_length=64)
    role: UserRole = UserRole.student


class LoginRequest(BaseModel):
    phone: str
    password: str


class OtpVerifyRequest(BaseModel):
    phone: str
    otp: str = Field(min_length=4, max_length=10)


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
