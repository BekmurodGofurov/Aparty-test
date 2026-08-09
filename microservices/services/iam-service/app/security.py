"""IAM Service — JWT helpers.

Uses PyJWT (not python-jose) as specified in the requirements.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import InvalidTokenError

from app.config import settings


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


def create_access_token(user_id: int) -> str:
    """Issue a short-lived access token (15 minutes by default)."""
    return _create_token(
        subject=str(user_id),
        expires_minutes=settings.access_token_expire_minutes,
        extra_claims={"type": "access"},
    )


def create_refresh_token(user_id: int) -> str:
    """Issue a long-lived refresh token (7 days by default)."""
    return _create_token(
        subject=str(user_id),
        expires_minutes=settings.refresh_token_expire_minutes,
        extra_claims={"type": "refresh"},
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
