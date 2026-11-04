"""Order Service Bookings Router (`/api/v1/bookings`). Booking requests only, no payments."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.catalog import CatalogUnavailableError, fetch_batch_booking_info, fetch_booking_info
from app.clients.iam import fetch_public_profiles
from app.constants import (
    ALL_ROLES,
    API_PREFIX,
    EVENT_BOOKING_CREATED,
    EVENT_BOOKING_UPDATED,
    RENTAL_TYPE_SHARED_ROOM,
)
from app.database import get_db
from app.events import publish_booking_event
from app.models import Booking, BookingStatus
from app.schemas import BookingCreate, BookingOut, BookingStatusUpdate, ListingBookingInfo, ListingBrief
from app.security import CurrentUser, get_current_user_id, require_roles

router = APIRouter(prefix=f"{API_PREFIX}/bookings", tags=["Bookings"])

ACTIVE_STATUSES = (BookingStatus.pending, BookingStatus.confirmed)
ACTIVE_LISTING_STATUS = "active"

# Allowed status changes per actor: {current status: statuses it can move to}.
OWNER_TRANSITIONS = {
    BookingStatus.pending: {BookingStatus.confirmed, BookingStatus.rejected, BookingStatus.cancelled},
    BookingStatus.confirmed: {BookingStatus.cancelled},
}
GUEST_TRANSITIONS = {
    BookingStatus.pending: {BookingStatus.cancelled},
    BookingStatus.confirmed: {BookingStatus.cancelled},
}
# People already living in the apartment can accept or decline a new roommate, nothing more.
RESIDENT_TRANSITIONS = {
    BookingStatus.pending: {BookingStatus.confirmed, BookingStatus.rejected},
}


def _error(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def _resident_apartment_ids(user_id: int):
    """Subquery: apartments where the user currently has a confirmed booking."""
    return select(Booking.apartment_listing_id).where(
        Booking.user_id == user_id,
        Booking.status == BookingStatus.confirmed,
        Booking.end_date >= date.today(),
    )


async def _is_resident(db: AsyncSession, user_id: int, apartment_id: uuid.UUID) -> bool:
    result = await db.execute(select(_resident_apartment_ids(user_id).where(
        Booking.apartment_listing_id == apartment_id
    ).exists()))
    return bool(result.scalar())


async def _confirmed_count(db: AsyncSession, listing_id: uuid.UUID) -> int:
    """Confirmed bookings of a listing that have not ended. Catalog uses it to mark a full roommate ad as occupied."""
    result = await db.execute(
        select(func.count()).select_from(Booking).where(
            Booking.listing_id == listing_id,
            Booking.status == BookingStatus.confirmed,
            Booking.end_date >= date.today(),
        )
    )
    return result.scalar_one()


async def _approver_ids(db: AsyncSession, booking: Booking) -> list[int]:
    """Who can answer this booking: the listing owner and, for a roommate request, everyone living in the apartment."""
    ids = {booking.listing_owner_id}
    if booking.is_roommate_request:
        residents = await db.execute(
            select(Booking.user_id).where(
                Booking.apartment_listing_id == booking.apartment_listing_id,
                Booking.status == BookingStatus.confirmed,
                Booking.end_date >= date.today(),
            )
        )
        ids.update(residents.scalars())
    ids.discard(booking.user_id)
    return sorted(ids)


async def _publish(db: AsyncSession, event: str, booking: Booking, actor_id: int) -> None:
    await publish_booking_event(
        event,
        booking,
        listing_confirmed_count=await _confirmed_count(db, booking.listing_id),
        actor_id=actor_id,
        approver_ids=await _approver_ids(db, booking),
    )


async def _get_booking(id: uuid.UUID, db: AsyncSession) -> Booking:
    booking = await db.get(Booking, id)
    if not booking:
        raise _error(status.HTTP_404_NOT_FOUND, "Booking not found.")
    return booking


async def _can_view(db: AsyncSession, booking: Booking, user_id: int) -> bool:
    if user_id in (booking.user_id, booking.listing_owner_id):
        return True
    return booking.is_roommate_request and await _is_resident(db, user_id, booking.apartment_listing_id)


async def _enrich_bookings(bookings: list[Booking]) -> list[BookingOut]:
    """Attach host and requester profiles from IAM, and listing info from Catalog."""
    if not bookings:
        return []

    user_ids = {b.user_id for b in bookings} | {b.listing_owner_id for b in bookings}
    profiles = await fetch_public_profiles(user_ids)

    listing_ids = {b.listing_id for b in bookings}
    listings_info = await fetch_batch_booking_info(listing_ids)

    enriched: list[BookingOut] = []
    for b in bookings:
        out = BookingOut.model_validate(b)
        out.requester = profiles.get(b.user_id)
        out.host = profiles.get(b.listing_owner_id)
        info = listings_info.get(b.listing_id)
        if info:
            out.listing = ListingBrief(
                id=info.id,
                title=info.title or b.listing_title or "",
                price=info.price,
                address=info.address,
                district=info.district,
                region=info.region,
                rooms_count=info.rooms_count,
                image_url=info.image_url,
                rental_type=info.rental_type,
            )
        elif b.listing_title:
            out.listing = ListingBrief(
                id=b.listing_id,
                title=b.listing_title,
            )
        enriched.append(out)

    return enriched


def _capacity(listing: ListingBookingInfo) -> int:
    """How many overlapping bookings a listing accepts: one for a whole unit, one per offered space otherwise."""
    if listing.parent_listing_id or listing.rental_type == RENTAL_TYPE_SHARED_ROOM:
        return listing.available_spaces
    return 1


@router.post("", status_code=status.HTTP_201_CREATED, response_model=BookingOut)
async def create_booking(
    payload: BookingCreate,
    user: CurrentUser = Depends(require_roles(*ALL_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> Booking:
    """Create a pending booking request for a listing."""
    user_id = user.id
    if payload.start_date >= payload.end_date:
        raise _error(status.HTTP_400_BAD_REQUEST, "End date must be after the start date.")
    if payload.start_date < date.today():
        raise _error(status.HTTP_400_BAD_REQUEST, "Start date cannot be in the past.")

    try:
        listing = await fetch_booking_info(payload.listing_id)
    except CatalogUnavailableError:
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "Catalog service is unavailable. Try again later.")

    if listing is None or listing.status != ACTIVE_LISTING_STATUS or not listing.is_active:
        raise _error(status.HTTP_404_NOT_FOUND, "Active listing not found.")
    if listing.owner_id == user_id:
        raise _error(status.HTTP_400_BAD_REQUEST, "You cannot book your own listing.")

    apartment_id = listing.parent_listing_id or listing.id
    is_roommate_request = listing.parent_listing_id is not None
    if is_roommate_request and await _is_resident(db, user_id, apartment_id):
        raise _error(status.HTTP_400_BAD_REQUEST, "You already live in this apartment.")

    # Serialize concurrent requests for the same listing so places cannot be over-booked.
    await db.execute(select(func.pg_advisory_xact_lock(func.hashtext(str(payload.listing_id)))))
    overlapping = and_(
        Booking.listing_id == payload.listing_id,
        Booking.status.in_(ACTIVE_STATUSES),
        Booking.start_date < payload.end_date,
        Booking.end_date > payload.start_date,
    )
    already_requested = await db.execute(select(Booking.id).where(overlapping, Booking.user_id == user_id).limit(1))
    if already_requested.first():
        raise _error(status.HTTP_409_CONFLICT, "You already have a booking for these dates.")
    taken = (await db.execute(select(func.count()).select_from(Booking).where(overlapping))).scalar_one()
    if taken >= _capacity(listing):
        raise _error(status.HTTP_409_CONFLICT, "The listing is fully booked for the selected dates.")

    nights = (payload.end_date - payload.start_date).days
    # Student housing rental prices are monthly. Prorate by 30-day calendar:
    total_price = round(nights * (listing.price / 30.0), 2)
    booking = Booking(
        listing_id=payload.listing_id,
        apartment_listing_id=apartment_id,
        is_roommate_request=is_roommate_request,
        listing_owner_id=listing.owner_id,
        listing_title=listing.title,
        user_id=user_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        total_price=total_price,
        status=BookingStatus.pending,
        message=payload.message,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    await _publish(db, EVENT_BOOKING_CREATED, booking, user_id)
    return booking


@router.get("", response_model=list[BookingOut])
async def list_my_bookings(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[BookingOut]:
    """Bookings requested by the authenticated user."""
    result = await db.execute(select(Booking).where(Booking.user_id == user_id).order_by(Booking.created_at.desc()))
    return await _enrich_bookings(list(result.scalars().all()))


@router.get("/incoming", response_model=list[BookingOut])
async def list_incoming_bookings(
    listing_id: Optional[uuid.UUID] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[BookingOut]:
    """Requests the user can answer: for their own listings, and roommate requests for the apartment they live in."""
    stmt = select(Booking).where(
        or_(
            Booking.listing_owner_id == user_id,
            and_(
                Booking.is_roommate_request,
                Booking.user_id != user_id,
                Booking.apartment_listing_id.in_(_resident_apartment_ids(user_id)),
            ),
        )
    )
    if listing_id:
        stmt = stmt.where(Booking.listing_id == listing_id)
    result = await db.execute(stmt.order_by(Booking.created_at.desc()))
    return await _enrich_bookings(list(result.scalars().all()))


@router.get("/{id}", response_model=BookingOut)
async def get_booking(
    id: uuid.UUID,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    booking = await _get_booking(id, db)
    if not await _can_view(db, booking, user_id):
        raise _error(status.HTTP_403_FORBIDDEN, "You do not have access to this booking.")
    return (await _enrich_bookings([booking]))[0]


@router.patch("/{id}/status", response_model=BookingOut)
async def update_booking_status(
    id: uuid.UUID,
    payload: BookingStatusUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    """Confirm, reject or cancel a booking, depending on who is asking."""
    booking = await _get_booking(id, db)

    if user_id == booking.listing_owner_id:
        transitions = OWNER_TRANSITIONS
    elif user_id == booking.user_id:
        transitions = GUEST_TRANSITIONS
    elif booking.is_roommate_request and await _is_resident(db, user_id, booking.apartment_listing_id):
        transitions = RESIDENT_TRANSITIONS
    else:
        raise _error(status.HTTP_403_FORBIDDEN, "You do not have access to this booking.")

    if payload.status not in transitions.get(booking.status, set()):
        raise _error(
            status.HTTP_409_CONFLICT,
            f"Cannot change a {booking.status.value} booking to {payload.status.value}.",
        )

    booking.status = payload.status
    await db.commit()
    await db.refresh(booking)

    await _publish(db, EVENT_BOOKING_UPDATED, booking, user_id)
    return (await _enrich_bookings([booking]))[0]
