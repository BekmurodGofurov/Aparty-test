"""Users domain — Core business logic and FastAPI auth dependencies.

Contains:
  - LoginCodeStore  : In-memory single-use 6-digit code store with 2-min TTL
  - get_current_user, get_optional_current_user, require_role : FastAPI auth deps
  - UserService     : User CRUD operations (Actor-Command preparation)

RULE: This file MUST NOT import SQLAlchemy models from any other domain.
"""

from __future__ import annotations

import logging
import secrets
import threading
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db, AsyncSessionLocal
from app.domains.users.models import User, UserRole, Notification, NotificationType

# Lazy import of database operations to avoid circular imports
from database.operations.select import users as select_users
from database.operations.update import users as update_users
from database.operations.delete import users as delete_users

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# OAuth2 scheme
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", auto_error=False
)


# ---------------------------------------------------------------------------
# In-memory Login Code Store
# ---------------------------------------------------------------------------

_store: dict[str, dict] = {}
_lock = threading.Lock()
LOGIN_CODE_TTL_SECONDS: int = 120  # 2 minutes


def generate_login_code(user_id: int) -> str:
    """Generate a unique 6-digit code bound to user_id with a 2-min TTL."""
    expires_at = time.monotonic() + LOGIN_CODE_TTL_SECONDS
    with _lock:
        for _ in range(10):
            code = f"{secrets.randbelow(1_000_000):06d}"
            if code not in _store:
                break
        _store[code] = {"user_id": user_id, "expires_at": expires_at}
    return code


def verify_and_consume_code(code: str) -> Optional[int]:
    """Validate the code and return the bound user_id, or None if invalid/expired."""
    with _lock:
        entry = _store.get(code)
        if entry is None:
            return None
        if time.monotonic() > entry["expires_at"]:
            _store.pop(code, None)
            return None
        _store.pop(code)
        return entry["user_id"]


def purge_expired() -> int:
    """Remove all expired entries. Returns the count removed."""
    now = time.monotonic()
    with _lock:
        expired = [k for k, v in _store.items() if now > v["expires_at"]]
        for k in expired:
            del _store[k]
    return len(expired)


# ---------------------------------------------------------------------------
# Auth dependency helpers
# ---------------------------------------------------------------------------


def _get_memory_admin_user() -> User:
    """Return an in-memory dummy User object representing the Root Admin."""
    return User(
        id=0,
        full_name="System Admin",
        phone="+998000000000",
        role=UserRole.admin,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: decode JWT and return the authenticated User."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        sub = payload.get("sub")
        role = payload.get("role")
        if sub is None:
            raise credentials_exception

        if str(sub).lower() == "admin" and str(role).lower() == "admin":
            return _get_memory_admin_user()

        user_id = int(sub)
    except (JWTError, ValueError) as exc:
        raise credentials_exception from exc

    user = await select_users.get_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_optional_current_user(
    token: str | None = Depends(optional_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """FastAPI dependency: return User if token valid, None otherwise."""
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        sub = payload.get("sub")
        role = payload.get("role")
        if sub is None:
            return None
        if str(sub).lower() == "admin" and str(role).lower() == "admin":
            return _get_memory_admin_user()
        user_id = int(sub)
    except (JWTError, ValueError):
        return None
    return await select_users.get_by_id(db, user_id)


def require_role(*role_names: str):
    """FastAPI dependency factory: require one of the specified roles."""

    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role is None or current_user.role.value not in role_names:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return checker


# Alias kept for backward compatibility with existing routers
require_roles = require_role


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: require admin role."""
    if current_user.role is None or current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required",
        )
    return current_user


# ---------------------------------------------------------------------------
# UserService — Actor-Command ready (future refactor target)
# ---------------------------------------------------------------------------


class UserService:
    """Business logic for user profile operations."""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        return await select_users.get_by_id(db, user_id)

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
        return await select_users.get_by_phone(db, phone)

    @staticmethod
    async def update_profile(
        db: AsyncSession, user: User, **fields
    ) -> Optional[User]:
        return await update_users.update_fields(db, user.id, **fields)

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        await delete_users.delete(db, user)

async def handle_order_placed(payload: dict) -> None:
    """
    Reacts to the 'order.placed' event.
    Handles user-specific logic (e.g. creating a notification).
    """
    user_id = payload.get("user_id")
    order_id = payload.get("order_id")
    owner_id = payload.get("owner_id")
    apartment_id = payload.get("apartment_id")
    message = payload.get("message")
    
    if not owner_id or not user_id:
        return
        
    async with AsyncSessionLocal() as db:
        try:
            notification = Notification(
                user_id=owner_id,
                actor_id=user_id,
                type=NotificationType.rental_request,
                title="Yangi band qilish so'rovi",
                body=message or "Sizga yangi band qilish so'rovi keldi",
                request_id=order_id,
                listing_id=apartment_id,
            )
            db.add(notification)
            await db.commit()
            logger.info(f"Notification created for User {owner_id} regarding Order: {order_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create notification for User {owner_id}: {e}")
            raise
