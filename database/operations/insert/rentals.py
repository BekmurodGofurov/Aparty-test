from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.rental import (
    MaintenanceReport,
    Rental,
    RentalRequest,
    RentalRequestMessage,
    RoomMessage,
)


async def create_rental(db: AsyncSession, rental: Rental) -> Rental:
    db.add(rental)
    await db.flush()
    return rental


async def create_rental_request(db: AsyncSession, request: RentalRequest) -> RentalRequest:
    db.add(request)
    await db.flush()
    return request


async def create_request_message(db: AsyncSession, message: RentalRequestMessage) -> RentalRequestMessage:
    db.add(message)
    return message


async def create_room_message(db: AsyncSession, message: RoomMessage) -> RoomMessage:
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def create_maintenance_report(db: AsyncSession, report: MaintenanceReport) -> MaintenanceReport:
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def create_notification(db: AsyncSession, notification: Notification) -> Notification:
    db.add(notification)
    return notification
