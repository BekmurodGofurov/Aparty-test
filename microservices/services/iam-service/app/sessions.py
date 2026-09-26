"""Opaque refresh-token sessions stored in Redis. Tokens rotate on every use."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Optional

from app.config import settings
from app.redis_client import get_redis

SESSION_KEY = "refresh:{digest}"


@dataclass(frozen=True)
class Session:
    subject: str
    role: Optional[str]


def _key(token: str) -> str:
    return SESSION_KEY.format(digest=hashlib.sha256(token.encode()).hexdigest())


async def create_session(subject: str, role: Optional[str]) -> str:
    """Store a new session and return its refresh token."""
    token = secrets.token_urlsafe(48)
    payload = json.dumps({"subject": subject, "role": role})
    await get_redis().set(_key(token), payload, ex=settings.refresh_token_expire_minutes * 60)
    return token


async def consume_session(token: str) -> Optional[Session]:
    """Atomically remove a session and return it. A token can be used only once."""
    raw = await get_redis().getdel(_key(token))
    if raw is None:
        return None
    data = json.loads(raw)
    return Session(subject=data["subject"], role=data["role"])


async def revoke_session(token: str) -> None:
    await get_redis().delete(_key(token))
