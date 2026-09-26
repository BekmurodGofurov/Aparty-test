"""Builders for the booking events published to RabbitMQ."""

from __future__ import annotations

from typing import Any

from app.models import Booking
from app.rabbitmq import publish_event


def booking_event_payload(event: str, booking: Booking, listing_confirmed_count: int = 0) -> dict[str, Any]:
    return {
        "event": event,
        "booking_id": str(booking.id),
        "listing_id": str(booking.listing_id),
        "apartment_listing_id": str(booking.apartment_listing_id),
        "is_roommate_request": booking.is_roommate_request,
        "listing_confirmed_count": listing_confirmed_count,
        "user_id": booking.user_id,
        "owner_id": booking.listing_owner_id,
        "start_date": booking.start_date.isoformat(),
        "end_date": booking.end_date.isoformat(),
        "total_price": booking.total_price,
        "status": booking.status.value,
    }


async def publish_booking_event(event: str, booking: Booking, listing_confirmed_count: int = 0) -> None:
    await publish_event(event, booking_event_payload(event, booking, listing_confirmed_count))
