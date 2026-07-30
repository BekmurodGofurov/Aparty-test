"""Orders domain — Core business logic (Actor-Command ready).

Contains:
  - premium_expiry_loop : Background task that expires overdue premium listings

RULE: This file MUST NOT import SQLAlchemy models from any other domain.
The Listing model is accessed via apartments domain's service layer when
a cross-domain read is required. The premium expiry DOES write to the
listings table — this is allowed because it's operating on a shared DB
schema concern that is owned by the apartments domain (Listing.is_premium).
We use raw SQL binding here to keep the write contained and avoid importing
the Listing ORM class directly.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict
from typing import Any, Optional

from app.core.database import AsyncSessionLocal
from app.core.events import publish
from app.domains.orders.models import RentalRequest, RentalRequestStatus

logger = logging.getLogger(__name__)


async def expire_premium_listings() -> None:
    """Bulk-update expired premium listings to is_premium=False.

    Uses a raw SQL UPDATE to avoid importing the Listing model from the
    apartments domain — this is the correct isolation approach.
    """
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        await db.execute(
            text(
                "UPDATE listings SET is_premium = FALSE "
                "WHERE is_premium = TRUE "
                "  AND premium_expires_at IS NOT NULL "
                "  AND premium_expires_at < :now"
            ),
            {"now": now},
        )
        await db.commit()
        logger.debug("Premium expiry check complete at %s.", now.isoformat())


async def premium_expiry_loop() -> None:
    """Infinite loop that expires premium listings every hour.

    Started as an ``asyncio.create_task()`` from ``core/lifespan.py``.
    """
    logger.info("Premium expiry daemon started (check interval: 3600s).")
    while True:
        await expire_premium_listings()
        await asyncio.sleep(3600)

class PlaceOrderCommand(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    requester_id: int
    apartment_id: int
    recipient_id: int
    message: Optional[str] = None

class OrderService:
    @staticmethod
    async def place_order(db: AsyncSession, command: PlaceOrderCommand) -> RentalRequest:
        new_request = RentalRequest(
            requester_id=command.requester_id,
            listing_id=command.apartment_id,
            recipient_id=command.recipient_id,
            message=command.message,
            status=RentalRequestStatus.pending,
        )
        
        db.add(new_request)
        await db.commit()
        await db.refresh(new_request)

        from app.core.contracts.events import OrderPlacedEvent
        event_payload = OrderPlacedEvent(
            order_id=new_request.id,
            apartment_id=command.apartment_id,
            user_id=command.requester_id,
            owner_id=command.recipient_id,
            message=command.message,
            status=new_request.status.value
        )
        
        await publish(event_payload.event_name, event_payload)
        
        return new_request
