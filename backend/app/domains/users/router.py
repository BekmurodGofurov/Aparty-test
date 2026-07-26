"""Users domain — FastAPI router.

Merges:
  - /auth/*           (register, login, refresh, logout, me, bot endpoints)
  - /users/*          (profile read/update/delete)
  - /notifications/*  (list, mark-read)

URL prefixes are assigned in main.py via include_router().
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Optional

from dotenv import dotenv_values
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import BACKEND_DIR, settings
from app.core.database import get_db
from app.core.security import create_token
from app.domains.users.models import User
from app.domains.users.schemas import (
    AdminLoginRequest,
    AuthSuccessResponse,
    BotLoginCodeRequest,
    BotLoginCodeResponse,
    CodeLoginRequest,
    NotificationListOut,
    NotificationOut,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    UserUpdate,
)
from app.domains.users.services import (
    UserService,
    generate_login_code,
    get_current_user,
    get_optional_current_user,
    require_role,
    verify_and_consume_code,
)
from database.operations.delete import users as delete_users
from database.operations.insert import users as insert_users
from database.operations.select import notifications as select_notifications
from database.operations.select import users as select_users
from database.operations.update import notifications as update_notifications
from database.operations.update import users as update_users

router = APIRouter()
logger = logging.getLogger(__name__)


# ===========================================================================
# Auth: helpers
# ===========================================================================


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_minutes * 60,
    )


# ===========================================================================
# Auth: registration
# ===========================================================================


@router.post(
    "/auth/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
async def register(
    payload: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> User:
    """Register a new user (called by the Telegram bot after FSM flow)."""
    from app.domains.users.models import UserRole

    if await select_users.get_by_id(db, payload.id) is not None:
        raise HTTPException(400, "User with this Telegram ID already exists")
    if await select_users.get_by_phone(db, payload.phone) is not None:
        raise HTTPException(400, "Phone number is already registered")
    if payload.role == UserRole.admin:
        raise HTTPException(400, "Cannot register with admin role")

    user = User(
        id=payload.id,
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        is_verified=True,
    )
    return await insert_users.create(db, user)


# ===========================================================================
# Auth: bot login code
# ===========================================================================


@router.post("/auth/bot/login-code", response_model=BotLoginCodeResponse, tags=["Auth"])
async def bot_generate_login_code(
    payload: BotLoginCodeRequest,
    db: AsyncSession = Depends(get_db),
) -> BotLoginCodeResponse:
    """Generate a single-use 6-digit login code for a registered user."""
    user = await select_users.get_by_id(db, payload.id)
    if user is None:
        raise HTTPException(
            404,
            "Bu Telegram akkaunt ro'yxatdan o'tmagan. Iltimos, /start bilan ro'yxatdan o'ting.",
        )
    code = generate_login_code(user.id)
    logger.info("Login code generated for user_id=%s", user.id)
    return BotLoginCodeResponse(code=code)


# ===========================================================================
# Auth: code login (React → backend)
# ===========================================================================


@router.post("/auth/login", response_model=AuthSuccessResponse, tags=["Auth"])
async def login(
    payload: CodeLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccessResponse:
    """Validate a 6-digit login code and issue JWT tokens."""
    user_id = verify_and_consume_code(payload.code)
    if user_id is None:
        raise HTTPException(400, "Kod noto'g'ri yoki muddati o'tgan. Iltimos, botdan yangi kod oling.")

    user = await select_users.get_by_id(db, user_id)
    if user is None:
        logger.error("Login code valid but user_id=%s not found in DB", user_id)
        raise HTTPException(404, "User not found")

    access_token = create_token(str(user.id), expires_minutes=settings.access_token_expire_minutes)
    refresh_token = create_token(str(user.id), expires_minutes=settings.refresh_token_expire_minutes)
    _set_refresh_cookie(response, refresh_token)

    logger.info("Login successful for user_id=%s", user.id)
    return AuthSuccessResponse(access_token=access_token)


# ===========================================================================
# Auth: admin login
# ===========================================================================


@router.post("/auth/admin-login", response_model=AuthSuccessResponse, tags=["Auth"])
async def admin_login(
    request: Request,
    response: Response,
    payload: Optional[AdminLoginRequest] = Body(default=None),
) -> AuthSuccessResponse:
    """Root Admin login — compares against environment variables."""
    username = payload.username if payload else None
    password = payload.password if payload else None

    if not username or not password:
        try:
            form = await request.form()
            username = username or form.get("username")
            password = password or form.get("password")
        except Exception:
            pass

    env_dict = dotenv_values(BACKEND_DIR / ".env")
    expected_username = env_dict.get("ADMIN_USERNAME") or os.getenv("ADMIN_USERNAME") or settings.admin_username
    expected_password = env_dict.get("ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD") or settings.admin_password

    if not username or not password or username != expected_username or password != expected_password:
        logger.warning("Failed root admin login attempt for username=%s", username)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_token("admin", expires_minutes=settings.access_token_expire_minutes, extra_claims={"role": "admin"})
    refresh_token = create_token("admin", expires_minutes=settings.refresh_token_expire_minutes, extra_claims={"role": "admin"})
    _set_refresh_cookie(response, refresh_token)
    logger.info("Root Admin logged in successfully")
    return AuthSuccessResponse(access_token=access_token)


# ===========================================================================
# Auth: token refresh & logout
# ===========================================================================


@router.post("/auth/refresh", response_model=TokenResponse, tags=["Auth"])
async def refresh_token(
    request: Request,
    payload: Optional[RefreshRequest] = Body(default=None),
) -> TokenResponse:
    """Refresh access token using the httpOnly refresh cookie."""
    token = request.cookies.get("refresh_token") or (payload.refresh_token if payload else None)
    if not token:
        raise HTTPException(401, "Refresh token missing")

    try:
        data = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = data.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid refresh token")
    except JWTError as exc:
        raise HTTPException(401, "Invalid refresh token") from exc

    return TokenResponse(
        message="Access token refreshed",
        access_token=create_token(str(user_id), expires_minutes=settings.access_token_expire_minutes),
    )


@router.post("/auth/logout", tags=["Auth"])
async def logout(response: Response) -> dict[str, object]:
    """Logout user — clear the refresh token cookie."""
    response.delete_cookie("refresh_token")
    return {"success": True, "message": "Logged out successfully"}


@router.get("/auth/me", response_model=UserOut, tags=["Auth"])
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Get the currently authenticated user."""
    return current_user


# ===========================================================================
# Auth: bot check endpoints
# ===========================================================================


@router.get("/auth/bot/check/{telegram_id}", tags=["Auth"])
async def check_user_by_telegram_id(
    telegram_id: int, db: AsyncSession = Depends(get_db)
) -> dict:
    """Check if a user is registered by their Telegram ID."""
    user = await select_users.get_by_id(db, telegram_id)
    if user:
        return {"success": True, "data": {"exists": True, "id": user.id, "full_name": user.full_name, "phone": user.phone, "role": user.role, "is_verified": user.is_verified}}
    return {"success": True, "data": {"exists": False}}


@router.get("/auth/bot/check/phone/{phone}", tags=["Auth"])
async def check_user_by_phone(phone: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Check if a user exists by phone number."""
    user = await select_users.get_by_phone(db, phone)
    if user:
        return {"success": True, "data": {"exists": True, "id": user.id, "full_name": user.full_name, "phone": user.phone, "role": user.role, "is_verified": user.is_verified}}
    return {"success": True, "data": {"exists": False}}


# ===========================================================================
# User profiles
# ===========================================================================


@router.get("/users/me", response_model=UserOut, tags=["Users"])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user profile."""
    return current_user


@router.get("/users/{user_id}", response_model=UserOut, tags=["Users"])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    """Get user by Telegram ID."""
    user = await select_users.get_by_id(db, user_id)
    if not user:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    return user


@router.put("/users/me", response_model=UserOut, tags=["Users"])
async def update_current_user(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update current user profile."""
    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop("role", None)
    update_data.pop("is_verified", None)
    if not update_data:
        return current_user
    updated = await update_users.update_fields(db, current_user.id, **update_data)
    if updated is None:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    return updated


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete current user account."""
    await delete_users.delete(db, current_user)
    return None


# ===========================================================================
# Notifications
# ===========================================================================


@router.get("/notifications/me", response_model=NotificationListOut, tags=["Notifications"])
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    notifications = await select_notifications.get_my_notifications(db, current_user.id)
    unread_count = await select_notifications.count_unread(db, current_user.id)
    return {"notifications": notifications, "unread_count": unread_count}


@router.patch("/notifications/{notification_id}/read", response_model=NotificationOut, tags=["Notifications"])
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = await select_notifications.get_by_id(db, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(404, "Notification topilmadi")
    return await update_notifications.mark_read(db, notification)


@router.patch("/notifications/read-all", tags=["Notifications"])
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await update_notifications.mark_all_read(db, current_user.id)
    return {"success": True}
