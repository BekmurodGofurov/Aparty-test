"""REST client for the IAM Service public profiles."""

from __future__ import annotations

import logging
from typing import Iterable, Optional

import httpx
from pydantic import BaseModel

from app.config import settings
from app.constants import API_PREFIX

logger = logging.getLogger(__name__)


class PublicProfile(BaseModel):
    id: int
    full_name: str
    phone: Optional[str] = None
    is_verified: bool = False


async def fetch_public_profiles(user_ids: Iterable[int]) -> dict[int, PublicProfile]:
    """Fetch public profiles by id. Returns an empty dict if IAM is unavailable."""
    ids = sorted(set(user_ids))
    if not ids:
        return {}

    url = f"{settings.iam_service_url}{API_PREFIX}/users/public"
    try:
        async with httpx.AsyncClient(timeout=settings.iam_request_timeout_seconds) as client:
            response = await client.get(url, params={"ids": ",".join(map(str, ids))})
            response.raise_for_status()
            return {item["id"]: PublicProfile(**item) for item in response.json()}
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        # Listings stay readable without owner details when IAM is down.
        logger.warning("IAM public profiles unavailable: %s", exc)
        return {}
