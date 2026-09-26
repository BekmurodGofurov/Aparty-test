"""Store a notification and deliver it to Telegram."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from app.database import AsyncSessionLocal
from app.models import Notification
from app.services import telegram
from app.services.templates import Message

logger = logging.getLogger(__name__)


async def notify(user_id: int, message: Message, dedupe_key: str) -> Optional[Notification]:
    """Create the notification unless this event already produced it, then send it to Telegram.

    Returns the notification, or None for a duplicate.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            insert(Notification)
            .values(
                user_id=user_id,
                type=message.type,
                title=message.title,
                body=message.body,
                target_url=message.target_url,
                dedupe_key=dedupe_key,
            )
            .on_conflict_do_nothing(index_elements=["dedupe_key"])
            .returning(Notification)
        )
        notification = result.scalar_one_or_none()
        await session.commit()
    if notification is None:
        logger.info("Duplicate notification skipped: %s", dedupe_key)
        return None

    status = await telegram.send_message(user_id, message.title, message.body, message.target_url)
    async with AsyncSessionLocal() as session:
        await session.execute(update(Notification).where(Notification.id == notification.id).values(telegram_status=status))
        await session.commit()
    notification.telegram_status = status
    return notification
