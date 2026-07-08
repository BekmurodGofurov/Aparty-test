import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationListOut, NotificationOut
from database.operations.select import notifications as select_notifications
from database.operations.update import notifications as update_notifications

router = APIRouter()


@router.get("/me", response_model=NotificationListOut)
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    notifications = await select_notifications.get_my_notifications(db, current_user.id)
    unread_count = await select_notifications.count_unread(db, current_user.id)
    return {"notifications": notifications, "unread_count": unread_count}


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Notification:
    notification = await select_notifications.get_by_id(db, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification topilmadi")
    return await update_notifications.mark_read(db, notification)


@router.patch("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await update_notifications.mark_all_read(db, current_user.id)
    return {"success": True}
