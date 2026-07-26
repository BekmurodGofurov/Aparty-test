"""Read-only Pydantic DTOs representing apartment data for cross-domain use.

These are the ONLY apartment-related types that the ``orders`` and ``users``
domains are allowed to import. They carry no SQLAlchemy dependency.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class ApartmentSummaryDTO(BaseModel):
    """Minimal apartment data needed by other domains (orders, reviews)."""

    id: uuid.UUID
    owner_id: int
    price_usd: int
    region: str
    district: str
    is_active: bool
    available_spaces: int


class ApartmentOwnerDTO(BaseModel):
    """Used by the orders domain to notify the owner after a booking event."""

    owner_id: int
    listing_id: uuid.UUID
    price_usd: int
