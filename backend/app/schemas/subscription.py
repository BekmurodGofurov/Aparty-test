from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.subscription import SubscriptionType


class SubscriptionPurchase(BaseModel):
    type: SubscriptionType
    start_date: date
    end_date: date
    listing_limit: int = Field(ge=1)


class SubscriptionOut(BaseModel):
    id: uuid.UUID
    user_id: int
    type: SubscriptionType
    start_date: date
    end_date: date
    listing_limit: int
    used_count: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
