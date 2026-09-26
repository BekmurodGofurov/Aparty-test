"""Turn domain events into notifications."""

from __future__ import annotations

import logging
from typing import Any, Iterable

from app.clients.iam import fetch_public_profiles
from app.constants import (
    BOOKING_CANCELLED,
    BOOKING_CONFIRMED,
    BOOKING_REJECTED,
    EVENT_BOOKING_CREATED,
    EVENT_BOOKING_UPDATED,
    EVENT_LISTING_CREATED,
    SOURCE_ROOMMATE,
)
from app.services import templates
from app.services.notifier import notify
from app.services.templates import Message

logger = logging.getLogger(__name__)


async def _requester_name(user_id: int) -> str | None:
    profile = (await fetch_public_profiles([user_id])).get(user_id)
    return profile.full_name if profile else None


async def _send_to(user_ids: Iterable[int], message: Message, key_prefix: str) -> None:
    for user_id in sorted(set(user_ids)):
        await notify(user_id, message, f"{key_prefix}:{user_id}")


async def _on_booking_created(payload: dict[str, Any]) -> None:
    approvers = payload.get("approver_ids") or []
    if not approvers:
        return
    message = templates.booking_requested(payload, await _requester_name(payload["user_id"]))
    await _send_to(approvers, message, f"booking.created:{payload['booking_id']}")


async def _on_booking_updated(payload: dict[str, Any]) -> None:
    status = payload.get("status")
    requester = payload["user_id"]
    key_prefix = f"booking.updated:{payload['booking_id']}:{status}"

    if status == BOOKING_CONFIRMED:
        await _send_to([requester], templates.booking_confirmed(payload), key_prefix)
    elif status == BOOKING_REJECTED:
        await _send_to([requester], templates.booking_rejected(payload), key_prefix)
    elif status == BOOKING_CANCELLED:
        if payload.get("actor_id") == requester:
            message = templates.cancelled_by_requester(payload, await _requester_name(requester))
            await _send_to(payload.get("approver_ids") or [], message, key_prefix)
        else:
            await _send_to([requester], templates.cancelled_by_other(payload), key_prefix)


async def _on_listing_created(payload: dict[str, Any]) -> None:
    owner_id = payload.get("apartment_owner_id")
    if payload.get("source") != SOURCE_ROOMMATE or not owner_id:
        return
    await _send_to([owner_id], templates.roommate_ad_posted(payload), f"listing.created:{payload['id']}")


HANDLERS = {
    EVENT_BOOKING_CREATED: _on_booking_created,
    EVENT_BOOKING_UPDATED: _on_booking_updated,
    EVENT_LISTING_CREATED: _on_listing_created,
}


async def handle_event(payload: dict[str, Any]) -> None:
    handler = HANDLERS.get(payload.get("event"))
    if handler is None:
        return
    await handler(payload)
