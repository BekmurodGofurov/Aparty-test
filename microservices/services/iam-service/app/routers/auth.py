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

from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserRole
from app.redis_client import save_otp, verify_and_consume_otp
from app.schemas import (
    AdminLoginRequest,
    AuthSuccessResponse,
    BotLoginCodeRequest,
    BotLoginCodeResponse,
    CodeLoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    UserUpdate,
)
from app.security import create_access_token, create_refresh_token, decode_token, get_current_user
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


def _delete_refresh_cookie(response: Response) -> None:
    """Remove the refresh token cookie on logout."""
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False,
        samesite="lax",
    )


async def _get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _get_user_by_phone(db: AsyncSession, phone: str) -> User | None:
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


def _admin_credentials_match(username: str, password: str) -> bool:
    """Compare local/test admin credentials using timing-safe comparisons."""
    username_matches = secrets.compare_digest(username, settings.admin_username)
    password_matches = secrets.compare_digest(password, settings.admin_password)
    return username_matches and password_matches


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


# ── Endpoint 4: Root Admin Login ──────────────────────────────────────────────


@router.post(
    "/auth/admin-login",
    response_model=AuthSuccessResponse,
    tags=["Auth"],
    summary="Authenticate the local/test root admin",
)
async def admin_login(
    payload: AdminLoginRequest,
    response: Response,
) -> AuthSuccessResponse:
    """Authenticate root admin credentials from environment variables.

    The returned synthetic admin identity is intended for auth/admin UI flows
    such as /users/me only. It is not a persisted database user and must not be
    used for actions that require a database foreign key.
    """
    if not _admin_credentials_match(payload.username, payload.password):
        logger.warning("Failed root admin login attempt for username=%s", payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token("admin", extra_claims={"role": "admin"})
    refresh_token = create_refresh_token("admin", extra_claims={"role": "admin"})
    _set_refresh_cookie(response, refresh_token)

    logger.info("Root admin logged in successfully")
    return AuthSuccessResponse(access_token=access_token)


# ── Endpoint 5: Refresh Access Token ──────────────────────────────────────────


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    tags=["Auth"],
    summary="Refresh an access token using the refresh cookie",
)
async def refresh_token(
    request: Request,
    payload: RefreshRequest | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Issue a fresh access token from the httpOnly refresh_token cookie."""
    token = request.cookies.get("refresh_token") or (payload.refresh_token if payload else None)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    try:
        data = decode_token(token)
        sub = data.get("sub")
        token_type = data.get("type")
        role = data.get("role")
        if sub is None or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    if str(sub).lower() == "admin" and str(role).lower() == "admin":
        new_token = create_access_token("admin", extra_claims={"role": "admin"})
        return TokenResponse(access_token=new_token)

    try:
        user_id = int(sub)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    if await _get_user_by_id(db, user_id) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return TokenResponse(access_token=create_access_token(user_id))


# ── Endpoint 6: Logout ────────────────────────────────────────────────────────


@router.post("/auth/logout", tags=["Auth"], summary="Clear the refresh token cookie")
async def logout(response: Response) -> dict[str, object]:
    """Log out the browser session by clearing the refresh token cookie."""
    _delete_refresh_cookie(response)
    return {"success": True, "message": "Logged out successfully"}


# ── Endpoint 7: Current User Profile ──────────────────────────────────────────


@router.get("/users/me", response_model=UserOut, tags=["Users"], summary="Get current user profile")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the authenticated user's profile."""
    return current_user


@router.get("/auth/me", response_model=UserOut, tags=["Auth"], summary="Get current user profile")
async def get_current_auth_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """Backward-compatible alias for the authenticated user's profile."""
    return current_user


# ── Endpoint 8: Update Current User Profile ───────────────────────────────────


@router.put("/users/me", response_model=UserOut, tags=["Users"], summary="Update current user profile")
async def update_current_user(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update profile fields for the authenticated database-backed user."""
    if current_user.id == 0 and current_user.role == UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Synthetic admin profile cannot be updated.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("old_password") or update_data.get("new_password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password changes are not supported for Telegram OTP accounts.",
        )

    mapped_updates = {
        "full_name": update_data.get("full_name") or update_data.get("ism"),
        "phone": update_data.get("phone") or update_data.get("telefon"),
        "university": update_data.get("university") or update_data.get("universitet"),
        "profile_picture_url": update_data.get("profile_picture_url") or update_data.get("rasm_url"),
    }
    cleaned_updates = {key: value for key, value in mapped_updates.items() if value is not None}
    if not cleaned_updates:
        return current_user

    new_phone = cleaned_updates.get("phone")
    if new_phone and new_phone != current_user.phone:
        existing = await _get_user_by_phone(db, new_phone)
        if existing is not None and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This phone number is already registered.",
            )

    for key, value in cleaned_updates.items():
        setattr(current_user, key, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


# ── Endpoint 9: Get User by ID ────────────────────────────────────────────────


@router.get("/users/{user_id}", response_model=UserOut, tags=["Users"], summary="Get user by Telegram ID")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return a user profile. Non-admin users can only fetch themselves."""
    is_admin = current_user.role == UserRole.admin
    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile.",
        )

    user = await _get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
