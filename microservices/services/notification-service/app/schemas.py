"""Notification Service Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PublicProfile(BaseModel):
    id: int
    full_name: str
    phone: Optional[str] = None
    is_verified: bool = False


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    title: str
    body: Optional[str] = None
    target_url: Optional[str] = None
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int


class MarkAllReadResponse(BaseModel):
    updated: int
