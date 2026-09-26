"""Access-token helpers and authentication dependencies."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import ACCESS_TOKEN_TYPE, ADMIN_SUBJECT, API_PREFIX
from app.database import get_db
from app.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/auth/admin-login")


def create_access_token(subject: int | str, role: Optional[str]) -> str:
    """Issue a short-lived access token that carries the user's role (None until chosen)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": ACCESS_TOKEN_TYPE,
        "role": role,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Validate signature, expiry, issuer, audience and token type."""
    claims = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        options={"require": ["exp", "iat", "iss", "aud", "sub"]},
    )
    if claims.get("type") != ACCESS_TOKEN_TYPE:
        raise InvalidTokenError("Not an access token")
    return claims


def synthetic_admin() -> User:
    """Root admin identity. It is not stored in the database."""
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
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = decode_access_token(token)
        if claims["sub"] == ADMIN_SUBJECT:
            if claims.get("role") != UserRole.admin.value:
                raise credentials_exception
            return synthetic_admin()
        user_id = int(claims["sub"])
    except (InvalidTokenError, ValueError) as exc:
        raise credentials_exception from exc

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user
