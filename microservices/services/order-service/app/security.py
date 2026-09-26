"""JWT authentication and role dependencies. Tokens are issued by the IAM Service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.config import settings
from app.constants import ACCESS_TOKEN_TYPE


@dataclass(frozen=True)
class CurrentUser:
    id: int
    role: Optional[str]


def _error(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def get_current_user(authorization: Optional[str] = Header(None, alias="Authorization")) -> CurrentUser:
    """Validate the Bearer access token and return the user id and role."""
    if not authorization or not authorization.startswith("Bearer "):
        raise _error(status.HTTP_401_UNAUTHORIZED, "Authorization Bearer token is required.")

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
        return CurrentUser(id=int(claims["sub"]), role=claims.get("role"))
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise _error(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token.") from exc


def get_current_user_id(user: CurrentUser = Depends(get_current_user)) -> int:
    return user.id


def require_roles(*roles: str) -> Callable[[CurrentUser], CurrentUser]:
    """Dependency factory: the caller must have chosen a role, and it must be one of `roles`."""

    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role is None:
            raise _error(status.HTTP_403_FORBIDDEN, "Choose a role before using this feature.")
        if user.role not in roles:
            raise _error(status.HTTP_403_FORBIDDEN, "Your role is not allowed to perform this action.")
        return user

    return checker
