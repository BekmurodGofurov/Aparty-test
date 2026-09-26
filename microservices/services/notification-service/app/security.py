"""JWT authentication dependency. Tokens are issued by the IAM Service."""

from __future__ import annotations

from typing import Optional

import jwt
from fastapi import Header, HTTPException, status

from app.config import settings
from app.constants import ACCESS_TOKEN_TYPE


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def get_current_user_id(authorization: Optional[str] = Header(None, alias="Authorization")) -> int:
    """Return the user id from a valid Bearer access token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthorized("Authorization Bearer token is required.")

    token = authorization.split(" ", 1)[1]
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
        if claims.get("type") != ACCESS_TOKEN_TYPE:
            raise jwt.InvalidTokenError("Not an access token")
        return int(claims["sub"])
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise _unauthorized("Invalid or expired token.") from exc
