"""Apartments domain — Core business logic (Actor-Command ready).

Contains:
  - ListingLimits  : Role-based listing quota rules
  - ApartmentService : Query/mutation methods returning DTOs (cross-domain safe)

RULE: This file MUST NOT import SQLAlchemy models from any other domain.
When other domains need apartment data, they call ApartmentService methods
which return ``app.core.contracts.apartment`` DTOs — never raw ORM objects.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
import logging

from app.core.contracts.apartment import ApartmentSummaryDTO
from app.domains.apartments.models import Listing
from app.core.database import AsyncSessionLocal

from database.operations.select import listings as select_listings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Listing limits (role-based quotas)
# ---------------------------------------------------------------------------

TRIAL_MONTHS = 6


@dataclass(frozen=True)
class ListingLimit:
    simple_limit: int
    premium_limit: int


def get_listing_limit_for_role(role_name: str) -> ListingLimit:
    """Get listing limits based on user role.

    - guest   : 0 simple, 0 premium
    - admin   : 100 simple, 100 premium (no effective limits)
    - makler  : 10 simple, 1 premium
    - owner   : 1 simple, 1 premium
    """
    if role_name == "owner":
        return ListingLimit(simple_limit=1, premium_limit=1)
    if role_name == "makler":
        return ListingLimit(simple_limit=10, premium_limit=1)
    if role_name == "admin":
        return ListingLimit(simple_limit=100, premium_limit=100)
    return ListingLimit(simple_limit=0, premium_limit=0)


# ---------------------------------------------------------------------------
# ApartmentService — cross-domain safe query interface
# ---------------------------------------------------------------------------


class ApartmentService:
    """Public service interface for the apartments domain.

    Other domains (orders, admin) MUST use these methods instead of
    importing Listing directly.  All public methods return Pydantic DTOs
    from ``app.core.contracts``.
    """

    @staticmethod
    async def get_summary(
        db: AsyncSession, listing_id: uuid.UUID
    ) -> Optional[ApartmentSummaryDTO]:
        """Return a minimal DTO for *listing_id*, or None if not found.

        Args:
            db: The current async database session.
            listing_id: The UUID of the listing to look up.

        Returns:
            ``ApartmentSummaryDTO`` or ``None``.
        """
        listing: Optional[Listing] = await select_listings.get_by_id(db, listing_id)
        if listing is None:
            return None
        return ApartmentSummaryDTO(
            id=listing.id,
            owner_id=listing.owner_id,
            price_usd=listing.price_usd,
            region=listing.region,
            district=listing.district,
            is_active=listing.is_active,
            available_spaces=listing.available_spaces,
        )

    @staticmethod
    def is_premium_active(
        is_premium: bool,
        premium_expires_at: Optional[datetime],
        now: Optional[datetime] = None,
    ) -> bool:
        """Check if a listing's premium status is currently active."""
        if not is_premium or premium_expires_at is None:
            return False
        now = now or datetime.now(timezone.utc)
        if premium_expires_at.tzinfo is None:
            premium_expires_at = premium_expires_at.replace(tzinfo=timezone.utc)
        return premium_expires_at > now

async def handle_order_placed(raw_payload: dict) -> None:
    """
    Reacts to the 'order.placed' event.
    Updates the apartment's availability status.
    """
    from app.core.contracts.events import OrderPlacedEvent
    
    # Validate contract
    payload = OrderPlacedEvent(**raw_payload)
    apartment_id = payload.apartment_id
        
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                update(Listing)
                .where(Listing.id == apartment_id)
                .values(is_available=False) # Example: marking unavailable on request
            )
            await db.execute(stmt)
            await db.commit()
            logger.info(f"Apartment {apartment_id} marked unavailable due to new order.")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update apartment {apartment_id}: {e}")
            raise
