"""IAM Service — JWT helpers.

Uses PyJWT (not python-jose) as specified in the requirements.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User, UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _create_token(
    subject: str,
    expires_minutes: int,
    extra_claims: Optional[dict] = None,
) -> str:
    """Internal helper: build a signed JWT."""
    now = datetime.now(timezone.utc)
    payload: dict = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int | str, extra_claims: Optional[dict] = None) -> str:
    """Issue a short-lived access token (15 minutes by default)."""
    claims = {"type": "access"}
    if extra_claims:
        claims.update(extra_claims)
    return _create_token(
        subject=str(user_id),
        expires_minutes=settings.access_token_expire_minutes,
        extra_claims=claims,
    )


def create_refresh_token(user_id: int | str, extra_claims: Optional[dict] = None) -> str:
    """Issue a long-lived refresh token (7 days by default)."""
    claims = {"type": "refresh"}
    if extra_claims:
        claims.update(extra_claims)
    return _create_token(
        subject=str(user_id),
        expires_minutes=settings.refresh_token_expire_minutes,
        extra_claims=claims,
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT.

    Raises jwt.InvalidTokenError (or a subclass) if invalid or expired.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def get_subject(token: str) -> Optional[str]:
    """Return the `sub` claim from a token, or None if decoding fails."""
    try:
        return decode_token(token).get("sub")
    except InvalidTokenError:
        return None


def get_memory_admin_user() -> User:
    """Return a synthetic Root Admin for auth/UI profile only.

    This object is not persisted and must not be used for DB foreign-key actions.
    """
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
    """Decode a Bearer access token and return the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        token_type = payload.get("type")
        role = payload.get("role")
        if sub is None or token_type != "access":
            raise credentials_exception
        if str(sub).lower() == "admin" and str(role).lower() == "admin":
            return get_memory_admin_user()
        user_id = int(sub)
    except (InvalidTokenError, ValueError) as exc:
        raise credentials_exception from exc

    result = await db.get(User, user_id)
    if result is None:
        raise credentials_exception
    return result


def require_role(*role_names: str):
    """Require the authenticated user to have one of the named roles."""

    async def checker(current_user: User = Depends(get_current_user)) -> User:
        role = current_user.role.value if current_user.role else None
        if role not in role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return checker
