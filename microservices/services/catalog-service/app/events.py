"""Builders for the listing events published to RabbitMQ."""

from __future__ import annotations

from typing import Any, Optional

from app.mappers import listing_image_urls, rental_type_from_property_type
from app.models import Listing
from app.rabbitmq import publish_event

LISTING_CREATED = "listing.created"
LISTING_UPDATED = "listing.updated"


def listing_event_payload(event: str, listing: Listing, apartment_owner_id: Optional[int] = None) -> dict[str, Any]:
    return {
        "event": event,
        "id": str(listing.id),
        "owner_id": listing.owner_id,
        "title": listing.title,
        "description": listing.description,
        "price": listing.price,
        "rental_type": rental_type_from_property_type(listing.property_type).value,
        "status": listing.status.value,
        "images": listing_image_urls(listing),
        "source": listing.source.value,
        "parent_listing_id": str(listing.parent_listing_id) if listing.parent_listing_id else None,
        "apartment_owner_id": apartment_owner_id,
    }


async def publish_listing_event(event: str, listing: Listing, apartment_owner_id: Optional[int] = None) -> None:
    await publish_event(event, listing_event_payload(event, listing, apartment_owner_id))
