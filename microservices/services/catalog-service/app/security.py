"""Catalog Service Security & Auth Dependency module.

Validates JWT tokens issued by IAM Service and extracts current owner_id.
"""

from __future__ import annotations

from typing import Optional
import jwt
from fastapi import Header, HTTPException, status

from app.config import settings


def get_current_owner_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> int:
    """Extract and return authenticated owner's user_id from Bearer token or gateway header."""
    if x_user_id:
        try:
            return int(x_user_id)
        except ValueError:
            pass

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentifikatsiyadan o'tilmagan. Authorization Bearer token talab qilinadi.",
        )

    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tarkibida foydalanuvchi ma'lumoti topilmadi.",
            )
        return int(sub)
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yaroqsiz yoki muddati o'tgan token.",
        ) from exc
