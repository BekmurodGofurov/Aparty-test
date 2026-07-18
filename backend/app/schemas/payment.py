from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    rental_id: uuid.UUID
    payer_id: Optional[int] = None
    amount: int = Field(ge=1)
    billing_month: date


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus


class PaymentUpdate(BaseModel):
    amount: int = Field(ge=1)
    billing_month: date
    status: PaymentStatus


class PaymentOut(BaseModel):
    id: uuid.UUID
    rental_id: uuid.UUID
    payer_id: Optional[int] = None
    amount: int
    billing_month: date
    status: PaymentStatus
    payment_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
