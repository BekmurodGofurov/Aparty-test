"""RabbitMQ consumers of the Catalog Service."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from app.constants import BOOKING_CONSUMER_QUEUE, BOOKING_UPDATED_ROUTING_KEY
from app.database import AsyncSessionLocal
from app.models import Listing, ListingSource, ListingStatus
from app.rabbitmq import start_consumer

logger = logging.getLogger(__name__)

CONSUMER_RETRY_SECONDS = 5


async def sync_roommate_listing_fullness(payload: dict[str, Any]) -> None:
    """Mark a roommate ad occupied once its places are filled, and reopen it when a place frees up."""
    if not payload.get("is_roommate_request") or not payload.get("listing_id"):
        return
    confirmed = int(payload.get("listing_confirmed_count", 0))

    async with AsyncSessionLocal() as session:
        listing = await session.get(Listing, uuid.UUID(payload["listing_id"]))
        if listing is None or listing.source != ListingSource.roommate:
            return

        if listing.status == ListingStatus.active and 0 < listing.available_spaces <= confirmed:
            listing.status = ListingStatus.rented
        elif listing.status == ListingStatus.rented and listing.available_spaces > confirmed:
            listing.status = ListingStatus.active
        else:
            return
        await session.commit()
        logger.info("Roommate ad %s is now %s", listing.id, listing.status.value)


async def handle_booking_event(payload: dict[str, Any]) -> None:
    await sync_roommate_listing_fullness(payload)


async def run_booking_consumer() -> None:
    """Keep trying to start the consumer until the broker is reachable."""
    while True:
        try:
            await start_consumer(BOOKING_CONSUMER_QUEUE, [BOOKING_UPDATED_ROUTING_KEY], handle_booking_event)
            return
        except Exception as exc:
            logger.warning("Booking consumer not started (%s). Retrying in %ss.", exc, CONSUMER_RETRY_SECONDS)
            await asyncio.sleep(CONSUMER_RETRY_SECONDS)
