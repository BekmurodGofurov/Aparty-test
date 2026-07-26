import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.orders.models import Rental, RentalRequest, RentalRequestStatus

from database.operations.select import rentals as select_rentals


async def deactivate_rental(db: AsyncSession, rental: Rental) -> Rental:
    rental.is_active = False
    await db.commit()
    await db.refresh(rental)
    return rental


async def accept_request(
    db: AsyncSession,
    request: RentalRequest,
    rental_id: uuid.UUID,
) -> RentalRequest:
    request.status = RentalRequestStatus.accepted
    request.rental_id = rental_id
    return request


async def reject_request(db: AsyncSession, request: RentalRequest) -> RentalRequest:
    request.status = RentalRequestStatus.rejected
    return request


async def reject_requests(db: AsyncSession, requests: list[RentalRequest]) -> None:
    for request in requests:
        request.status = RentalRequestStatus.rejected
