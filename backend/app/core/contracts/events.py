"""Domain Event Contracts.

Strict Pydantic schemas for cross-domain event payloads.
Ensures consumers receive well-formed, typed data instead of raw dicts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base schema for all domain events."""
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_name: str


class OrderPlacedEvent(BaseEvent):
    """Event emitted when a user places a rental request for an apartment."""
    event_name: str = "order.placed"
    
    order_id: int
    apartment_id: int
    user_id: int
    owner_id: int
    message: Optional[str] = None
    status: str
