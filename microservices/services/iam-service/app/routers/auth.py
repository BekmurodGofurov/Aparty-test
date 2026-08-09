"""IAM Service — Authentication router.

Endpoints
─────────
POST /api/v1/auth/bot/register
    Registers a new user in Neon DB.  Called by the Telegram bot.

POST /api/v1/auth/bot/login-code
    Generates a 6-digit OTP, stores it in Redis (TTL 120 s), and
    returns it to the bot so the bot can display it to the user.

POST /api/v1/auth/login
    Accepts the 6-digit code from the React frontend, validates it
    against Redis, issues a JWT access token + refresh token.
"""

from __future__ import annotations

import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.redis_client import save_otp, verify_and_consume_otp
from app.schemas import (
    AuthSuccessResponse,
    BotLoginCodeRequest,
    BotLoginCodeResponse,
    CodeLoginRequest,
    RegisterRequest,
    UserOut,
)
from app.security import create_access_token, create_refresh_token
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Attach the refresh token as an httpOnly cookie."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,          # Set to True in production (HTTPS)
        samesite="lax",
        max_age=settings.refresh_token_expire_minutes * 60,
    )


async def _get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _get_user_by_phone(db: AsyncSession, phone: str) -> User | None:
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


def _generate_otp_code() -> str:
    """Return a cryptographically random, zero-padded 6-digit string."""
    return f"{secrets.randbelow(1_000_000):06d}"


# ── Endpoint 1: Bot Registration ──────────────────────────────────────────────


@router.post(
    "/auth/bot/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
    summary="Register a new user (called by Telegram bot)",
)
async def bot_register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Save a new user to Neon DB.

    - Rejects duplicate Telegram IDs (400).
    - Rejects duplicate phone numbers (400).
    - Sets is_verified=True immediately (phone ownership confirmed via Telegram contact).
    - Never stores a password.
    """
    # Duplicate Telegram ID guard
    if await _get_user_by_id(db, payload.id) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this Telegram ID already exists.",
        )

    # Duplicate phone guard
    if await _get_user_by_phone(db, payload.phone) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This phone number is already registered.",
        )

    # Admin role cannot be self-assigned
    if payload.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register with the admin role.",
        )

    user = User(
        id=payload.id,
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        is_verified=True,   # Phone ownership is proven by Telegram's contact share
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("New user registered: id=%s phone=%s role=%s", user.id, user.phone, user.role)
    return user


# ── Endpoint 2: Generate OTP (Bot Login Code) ─────────────────────────────────


@router.post(
    "/auth/bot/login-code",
    response_model=BotLoginCodeResponse,
    tags=["Auth"],
    summary="Generate a 6-digit OTP and store it in Redis (called by Telegram bot)",
)
async def bot_generate_login_code(
    payload: BotLoginCodeRequest,
    db: AsyncSession = Depends(get_db),
) -> BotLoginCodeResponse:
    """Generate a single-use 6-digit OTP for the given Telegram user.

    The code is stored in Redis under two keys (forward + reverse) with a
    120-second TTL.  The bot displays the code to the user; the backend
    never sends anything directly to Telegram.
    """
    # Verify the user exists
    user = await _get_user_by_id(db, payload.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "This Telegram account is not registered. "
                "Please start the bot and complete registration first."
            ),
        )

    code = _generate_otp_code()
    await save_otp(user.id, code)

    logger.info("OTP generated for user_id=%s (TTL=%ss)", user.id, settings.otp_ttl_seconds)
    return BotLoginCodeResponse(code=code)


# ── Endpoint 3: Verify OTP and Issue JWT ──────────────────────────────────────


@router.post(
    "/auth/login",
    response_model=AuthSuccessResponse,
    tags=["Auth"],
    summary="Verify 6-digit OTP and issue JWT tokens (called by React frontend)",
)
async def login(
    payload: CodeLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccessResponse:
    """Validate the OTP from the frontend, delete it from Redis, and issue JWTs.

    Steps:
    1. Reverse-lookup the user_id from otp_code:{code} in Redis.
    2. Delete both Redis keys atomically (single-use enforcement).
    3. Fetch the user from Neon DB.
    4. Issue access token (15 min) and refresh token (7 days).
    5. Set refresh token as an httpOnly cookie.
    6. Return access token in the response body.
    """
    # Verify OTP against Redis and consume it (atomic delete on success)
    user_id = await verify_and_consume_otp(payload.code)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code. Please request a new one from the bot.",
        )

    # Fetch full user record from Neon DB
    user = await _get_user_by_id(db, user_id)
    if user is None:
        # Should never happen, but guard against data inconsistency
        logger.error("OTP valid but user_id=%s not found in DB", user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Issue tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Attach refresh token as httpOnly cookie
    _set_refresh_cookie(response, refresh_token)

    logger.info("Login successful for user_id=%s", user.id)
    return AuthSuccessResponse(access_token=access_token)
