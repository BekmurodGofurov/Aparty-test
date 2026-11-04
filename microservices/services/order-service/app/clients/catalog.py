"""REST client for the Catalog Service."""

from __future__ import annotations

import logging
import uuid
from typing import Iterable, Optional

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


async def fetch_batch_booking_info(listing_ids: Iterable[uuid.UUID]) -> dict[uuid.UUID, ListingBookingInfo]:
    """Fetch booking info for multiple listings. Returns an empty dict if Catalog is unavailable."""
    unique_ids = list({lid for lid in listing_ids if lid})
    if not unique_ids:
        return {}

    url = f"{settings.catalog_service_url}{API_PREFIX}/listings/batch/booking-info"
    try:
        async with httpx.AsyncClient(timeout=settings.catalog_request_timeout_seconds) as client:
            response = await client.get(url, params={"ids": ",".join(str(i) for i in unique_ids)})
            if response.status_code == 200:
                return {
                    uuid.UUID(str(item["id"])): ListingBookingInfo(**item)
                    for item in response.json()
                }
    except Exception as exc:
        logger.warning("Batch booking-info endpoint failed: %s, falling back to individual calls", exc)

    # Fallback: query individually
    results: dict[uuid.UUID, ListingBookingInfo] = {}
    for lid in unique_ids:
        try:
            info = await fetch_booking_info(lid)
            if info:
                results[lid] = info
        except Exception:
            pass
    return results
