import uuid
from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.rental import (
    MaintenanceReport,
    Rental,
    RentalRequest,
    RentalRequestMessage,
    RentalRequestStatus,
    RoomMessage,
)
from app.models.user import User


async def get_rental_by_id(db: AsyncSession, rental_id: uuid.UUID) -> Optional[Rental]:
    return await db.get(Rental, rental_id)


async def get_by_listing_id(
    db: AsyncSession,
    listing_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Rental]:
    result = await db.execute(
        select(Rental).where(Rental.listing_id == listing_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_by_student_id(
    db: AsyncSession,
    student_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Rental]:
    result = await db.execute(
        select(Rental).where(Rental.student_id == student_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_active_rentals(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Rental]:
    result = await db.execute(
        select(Rental).where(Rental.is_active.is_(True)).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_by_listing_and_student(
    db: AsyncSession,
    listing_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Optional[Rental]:
    result = await db.execute(
        select(Rental).where(
            and_(Rental.listing_id == listing_id, Rental.student_id == student_id)
        )
    )
    return result.scalar_one_or_none()


async def count_active_by_student(db: AsyncSession, student_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count(Rental.id)).where(
                Rental.student_id == student_id,
                Rental.is_active.is_(True),
            )
        )
        or 0
    )


async def count_roommates(
    db: AsyncSession,
    listing_id: uuid.UUID,
    student_id: uuid.UUID,
) -> int:
    return (
        await db.scalar(
            select(func.count(Rental.id)).where(
                Rental.listing_id == listing_id,
                Rental.student_id == student_id,
                Rental.is_active.is_(True),
            )
        )
        or 0
    )


async def get_owner_rental_rows(db: AsyncSession, owner_id: uuid.UUID) -> list[tuple[Rental, Listing, User]]:
    result = await db.execute(
        select(Rental, Listing, User)
        .join(Listing, Rental.listing_id == Listing.id)
        .join(User, Rental.student_id == User.id)
        .where(Listing.owner_id == owner_id)
        .order_by(desc(Rental.is_active), desc(Rental.created_at))
    )
    return list(result.all())


async def get_my_room_rows(db: AsyncSession, student_id: uuid.UUID) -> list[tuple[Rental, Listing, User]]:
    result = await db.execute(
        select(Rental, Listing, User)
        .join(Listing, Rental.listing_id == Listing.id)
        .join(User, Listing.owner_id == User.id)
        .where(Rental.student_id == student_id, Rental.is_active.is_(True))
        .order_by(desc(Rental.created_at))
    )
    return list(result.all())


async def get_neighbors(db: AsyncSession, listing_id: uuid.UUID, exclude_user_id: uuid.UUID) -> list[User]:
    result = await db.execute(
        select(User)
        .join(Rental, Rental.student_id == User.id)
        .where(
            Rental.listing_id == listing_id,
            Rental.is_active.is_(True),
            User.id != exclude_user_id,
        )
        .order_by(User.full_name)
    )
    return list(result.scalars().all())


# Rental requests

async def get_request_by_id(db: AsyncSession, request_id: uuid.UUID) -> Optional[RentalRequest]:
    return await db.get(RentalRequest, request_id)


async def get_requests_by_requester(db: AsyncSession, requester_id: uuid.UUID) -> list[RentalRequest]:
    result = await db.execute(
        select(RentalRequest)
        .where(RentalRequest.requester_id == requester_id)
        .order_by(desc(RentalRequest.created_at))
    )
    return list(result.scalars().all())


async def get_requests_inbox(db: AsyncSession, recipient_id: uuid.UUID) -> list[RentalRequest]:
    result = await db.execute(
        select(RentalRequest)
        .where(RentalRequest.recipient_id == recipient_id)
        .order_by(
            desc(RentalRequest.status == RentalRequestStatus.pending),
            desc(RentalRequest.created_at),
        )
    )
    return list(result.scalars().all())


async def get_conversations(db: AsyncSession, user_id: uuid.UUID) -> list[RentalRequest]:
    result = await db.execute(
        select(RentalRequest)
        .where(
            (RentalRequest.requester_id == user_id) | (RentalRequest.recipient_id == user_id)
        )
        .order_by(desc(RentalRequest.updated_at), desc(RentalRequest.created_at))
    )
    return list(result.scalars().all())


async def get_pending_duplicate(
    db: AsyncSession,
    listing_id: uuid.UUID,
    requester_id: uuid.UUID,
) -> Optional[RentalRequest]:
    return await db.scalar(
        select(RentalRequest).where(
            RentalRequest.listing_id == listing_id,
            RentalRequest.requester_id == requester_id,
            RentalRequest.status == RentalRequestStatus.pending,
        )
    )


async def count_pending_by_requester(db: AsyncSession, requester_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count(RentalRequest.id)).where(
                RentalRequest.requester_id == requester_id,
                RentalRequest.status == RentalRequestStatus.pending,
            )
        )
        or 0
    )


async def get_pending_by_requester_excluding(
    db: AsyncSession,
    requester_id: uuid.UUID,
    exclude_request_id: uuid.UUID,
) -> list[RentalRequest]:
    result = await db.execute(
        select(RentalRequest).where(
            RentalRequest.requester_id == requester_id,
            RentalRequest.id != exclude_request_id,
            RentalRequest.status == RentalRequestStatus.pending,
        )
    )
    return list(result.scalars().all())


async def get_pending_for_listing_excluding(
    db: AsyncSession,
    listing_id: uuid.UUID,
    exclude_request_id: uuid.UUID,
) -> list[RentalRequest]:
    result = await db.execute(
        select(RentalRequest).where(
            RentalRequest.listing_id == listing_id,
            RentalRequest.id != exclude_request_id,
            RentalRequest.status == RentalRequestStatus.pending,
        )
    )
    return list(result.scalars().all())


async def get_request_messages(
    db: AsyncSession,
    request_id: uuid.UUID,
) -> list[tuple[RentalRequestMessage, User]]:
    result = await db.execute(
        select(RentalRequestMessage, User)
        .join(User, RentalRequestMessage.sender_id == User.id)
        .where(RentalRequestMessage.request_id == request_id)
        .order_by(RentalRequestMessage.created_at)
    )
    return list(result.all())


async def get_room_messages(
    db: AsyncSession,
    listing_id: uuid.UUID,
) -> list[tuple[RoomMessage, User]]:
    result = await db.execute(
        select(RoomMessage, User)
        .join(User, RoomMessage.sender_id == User.id)
        .where(RoomMessage.listing_id == listing_id)
        .order_by(RoomMessage.created_at)
    )
    return list(result.all())
