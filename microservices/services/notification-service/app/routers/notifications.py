"""Notification Service router (`/api/v1/notifications`). Every user sees only their own notifications."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import API_PREFIX
from app.database import get_db
from app.models import Notification
from app.schemas import MarkAllReadResponse, NotificationListResponse, NotificationOut
from app.security import get_current_user_id

router = APIRouter(prefix=f"{API_PREFIX}/notifications", tags=["Notifications"])


@router.get("/me", response_model=NotificationListResponse)
async def list_my_notifications(
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    unread_only: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    """Newest first, plus the total number of unread notifications (not just those returned)."""
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    items = (await db.execute(stmt.order_by(Notification.created_at.desc()).limit(limit))).scalars().all()

    unread_count = (
        await db.execute(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user_id, Notification.is_read.is_(False)
            )
        )
    ).scalar_one()
    return NotificationListResponse(
        notifications=[NotificationOut.model_validate(item) for item in items], unread_count=unread_count
    )


@router.patch("/read-all", response_model=MarkAllReadResponse)
async def mark_all_read(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MarkAllReadResponse:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return MarkAllReadResponse(updated=result.rowcount)


@router.patch("/{id}/read", response_model=NotificationOut)
async def mark_read(
    id: uuid.UUID,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Notification:
    notification = await db.get(Notification, id)
    if notification is None or notification.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await db.commit()
    return notification
