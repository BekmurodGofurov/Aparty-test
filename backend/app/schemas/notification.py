from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    type: NotificationType
    title: str
    body: Optional[str] = None
    request_id: Optional[uuid.UUID] = None
    listing_id: Optional[uuid.UUID] = None
    target_url: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListOut(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int
