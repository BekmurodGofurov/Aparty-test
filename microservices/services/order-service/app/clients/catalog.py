"""REST client for the Catalog Service."""

from __future__ import annotations

import logging
import uuid
from typing import Optional

import httpx

from app.config import settings
from app.constants import API_PREFIX
from app.schemas import ListingBookingInfo

logger = logging.getLogger(__name__)


class CatalogUnavailableError(Exception):
    """The Catalog Service could not be reached or returned an unexpected response."""


async def fetch_booking_info(listing_id: uuid.UUID) -> Optional[ListingBookingInfo]:
    """Return booking-relevant listing data, or None if the listing does not exist."""
    url = f"{settings.catalog_service_url}{API_PREFIX}/listings/{listing_id}/booking-info"
    try:
        async with httpx.AsyncClient(timeout=settings.catalog_request_timeout_seconds) as client:
            response = await client.get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return ListingBookingInfo(**response.json())
    except (httpx.HTTPError, ValueError) as exc:
        logger.error("Catalog Service unavailable: %s", exc)
        raise CatalogUnavailableError from exc
