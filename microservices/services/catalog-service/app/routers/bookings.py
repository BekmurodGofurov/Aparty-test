"""Catalog Service Bookings & Orders Router (`/api/v1/bookings`)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Booking, BookingStatus, Listing, ListingStatus
from app.rabbitmq import publish_event
from app.schemas import BookingCreate, BookingOut, BookingStatusUpdate
from app.security import get_current_owner_id

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings & Orders"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=BookingOut)
async def create_booking(
    payload: BookingCreate,
    user_id: int = Depends(get_current_owner_id),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    """Yangi bron (booking) so'rovini yaratish va band kunlarni tekshirish."""
    if payload.start_date >= payload.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak.",
        )

    if payload.start_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Boshlanish sanasi bugungi kundan oldin bo'lishi mumkin emas.",
        )

    # 1. Check if listing exists and is active
    stmt = select(Listing).where(Listing.id == payload.listing_id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing or listing.status != ListingStatus.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faol e'lon topilmadi.",
        )

    if listing.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O'zingizning e'loningizni bron qila olmaysiz.",
        )

    # 2. Check for overlapping existing active/pending bookings
    overlap_stmt = select(Booking).where(
        and_(
            Booking.listing_id == payload.listing_id,
            Booking.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
            or_(
                and_(Booking.start_date <= payload.start_date, Booking.end_date > payload.start_date),
                and_(Booking.start_date < payload.end_date, Booking.end_date >= payload.end_date),
                and_(Booking.start_date >= payload.start_date, Booking.end_date <= payload.end_date),
            ),
        )
    )
    overlap_result = await db.execute(overlap_stmt)
    existing_booking = overlap_result.scalar_one_or_none()

    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ushbu ko'rsatilgan sanalarda e'lon allaqachon band qilingan.",
        )

    # 3. Calculate total price
    days = (payload.end_date - payload.start_date).days
    total_price = days * listing.price

    # 4. Create booking record
    new_booking = Booking(
        listing_id=payload.listing_id,
        user_id=user_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        total_price=total_price,
        status=BookingStatus.pending,
        message=payload.message,
    )
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)

    # 5. Publish RabbitMQ event
    event_payload = {
        "event": "booking.created",
        "booking_id": str(new_booking.id),
        "listing_id": str(new_booking.listing_id),
        "user_id": new_booking.user_id,
        "owner_id": listing.owner_id,
        "start_date": str(new_booking.start_date),
        "end_date": str(new_booking.end_date),
        "total_price": new_booking.total_price,
        "status": new_booking.status.value,
    }
    await publish_event("booking.created", event_payload)

    return new_booking


@router.get("", response_model=List[BookingOut])
async def list_bookings(
    listing_id: Optional[uuid.UUID] = None,
    current_user_id: int = Depends(get_current_owner_id),
    db: AsyncSession = Depends(get_db),
) -> List[BookingOut]:
    """Foydalanuvchining bron so'rovlari yoki e'longa tegishli bronlar ro'yxatini olish."""
    stmt = select(Booking)
    if listing_id:
        stmt = stmt.where(Booking.listing_id == listing_id)
    else:
        stmt = stmt.where(Booking.user_id == current_user_id)

    stmt = stmt.order_by(Booking.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{id}", response_model=BookingOut)
async def get_booking(
    id: uuid.UUID,
    current_user_id: int = Depends(get_current_owner_id),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    """ID bo'yicha bron ma'lumotlarini olish."""
    stmt = select(Booking).options(selectinload(Booking.listing)).where(Booking.id == id)
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bron so'rovi topilmadi.",
        )

    if booking.user_id != current_user_id and booking.listing.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ushbu bron so'rovini ko'rishga ruxsat yo'q.",
        )

    return booking


@router.patch("/{id}/status", response_model=BookingOut)
async def update_booking_status(
    id: uuid.UUID,
    payload: BookingStatusUpdate,
    current_user_id: int = Depends(get_current_owner_id),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    """Bron statusini tahrirlash (tasdiqlash, rad etish yoki bekor qilish)."""
    stmt = select(Booking).options(selectinload(Booking.listing)).where(Booking.id == id)
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bron so'rovi topilmadi.",
        )

    is_owner = booking.listing.owner_id == current_user_id
    is_requester = booking.user_id == current_user_id

    if not is_owner and not is_requester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ushbu bron so'rovini o'zgartirishga ruxsat yo'q.",
        )

    if is_requester and payload.status not in [BookingStatus.cancelled]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mijoz faqat o'z so'rovini bekor qilishi mumkin.",
        )

    booking.status = payload.status
    await db.commit()
    await db.refresh(booking)

    # Publish RabbitMQ event
    event_payload = {
        "event": "booking.updated",
        "booking_id": str(booking.id),
        "listing_id": str(booking.listing_id),
        "user_id": booking.user_id,
        "owner_id": booking.listing.owner_id,
        "status": booking.status.value,
    }
    await publish_event("booking.updated", event_payload)

    return booking
