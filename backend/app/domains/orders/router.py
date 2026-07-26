"""Orders domain — FastAPI router.

Merges:
  - /rentals/*       (rental CRUD, requests, conversations, room chat)
  - /payments/*      (payment CRUD)
  - /reviews/*       (listing reviews)
  - /subscriptions/* (makler subscription plans)

URL prefixes are assigned in main.py via include_router().
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.orders.models import (
    MaintenanceReport,
    MaintenanceReportStatus,
    Payment,
    Rental,
    RentalRequest,
    RentalRequestMessage,
    RentalRequestStatus,
    Review,
    RoomMessage,
    Subscription,
    SubscriptionType,
)
from app.domains.orders.schemas import (
    MaintenanceReportCreate,
    MaintenanceReportOut,
    MyRoomOut,
    OwnerRentalOut,
    PaymentCreate,
    PaymentOut,
    PaymentStatusUpdate,
    PaymentUpdate,
    RentalCreate,
    RentalMessageCreate,
    RentalOut,
    RentalRequestCreate,
    RentalRequestMessageOut,
    RentalRequestOut,
    ReviewCreate,
    ReviewOut,
    RoomMessageOut,
    SubscriptionOut,
    SubscriptionPurchase,
    VacancyRepostCreate,
)
from app.domains.users.models import User, UserRole
from app.domains.users.services import get_current_user, require_role, require_roles
from app.domains.apartments.models import Listing, ListingSource
from database.operations.delete import payments as delete_payments
from database.operations.delete import reviews as delete_reviews
from database.operations.insert import listings as insert_listings
from database.operations.insert import payments as insert_payments
from database.operations.insert import rentals as insert_rentals
from database.operations.insert import reviews as insert_reviews
from database.operations.insert import subscriptions as insert_subscriptions
from database.operations.select import listings as select_listings
from database.operations.select import payments as select_payments
from database.operations.select import rentals as select_rentals
from database.operations.select import reviews as select_reviews
from database.operations.select import subscriptions as select_subscriptions
from database.operations.select import users as select_users
from database.operations.update import listings as update_listings
from database.operations.update import payments as update_payments
from database.operations.update import rentals as update_rentals
from database.operations.update import subscriptions as update_subscriptions
from app.domains.users.models import Notification, NotificationType

router = APIRouter()


# ===========================================================================
# Helpers
# ===========================================================================


def _user_payload(user: User) -> dict:
    return {"id": user.id, "full_name": user.full_name, "phone": user.phone, "is_verified": user.is_verified}


def _listing_payload(listing: Listing) -> dict:
    return {
        "id": listing.id, "region": listing.region, "district": listing.district,
        "address": listing.address, "price_usd": listing.price_usd,
        "images": listing.images[:1] if listing.images else [],
    }


def _next_payment_date(start_date: date) -> date:
    today = date.today()
    month, year = today.month, today.year
    day = min(start_date.day, 28)
    next_date = date(year, month, day)
    if next_date < today:
        month += 1
        if month > 12:
            month, year = 1, year + 1
        next_date = date(year, month, day)
    return next_date


def _notification_target(request_id) -> str:
    return f"/messages?request={request_id}"


async def _add_notification(db, *, user_id, actor_id, type, title, body=None, request_id=None, listing_id=None):
    await insert_rentals.create_notification(
        db,
        Notification(
            user_id=user_id, actor_id=actor_id, type=type, title=title, body=body,
            request_id=request_id, listing_id=listing_id,
            target_url=_notification_target(request_id) if request_id else "/messages",
        ),
    )


async def _request_payload(db, request: RentalRequest) -> dict:
    listing = await select_listings.get_by_id(db, request.listing_id)
    requester = await select_users.get_by_id(db, request.requester_id)
    recipient = await select_users.get_by_id(db, request.recipient_id)
    return {
        "id": request.id, "listing_id": request.listing_id,
        "requester": _user_payload(requester), "recipient": _user_payload(recipient),
        "listing": _listing_payload(listing), "status": request.status,
        "message": request.message, "rental_id": request.rental_id,
        "created_at": request.created_at, "updated_at": request.updated_at,
    }


async def _conversation_payload(db, request: RentalRequest, current_user: User) -> dict:
    payload = await _request_payload(db, request)
    rows = await select_rentals.get_request_messages(db, request.id)
    messages = [
        {"id": m.id, "request_id": m.request_id, "sender_id": m.sender_id,
         "sender_name": sender.full_name, "text": m.text, "created_at": m.created_at}
        for m, sender in rows
    ]
    other = payload["recipient"] if request.requester_id == current_user.id else payload["requester"]
    return {**payload, "other_user": other, "messages": messages, "last_message": messages[-1] if messages else None}


async def _can_access_request(request: RentalRequest, user: User) -> bool:
    return user.id in {request.requester_id, request.recipient_id} or user.role == UserRole.admin


async def _can_access_rental(db, rental: Rental, user: User) -> bool:
    listing = await select_listings.get_by_id(db, rental.listing_id)
    if rental.student_id == user.id or (listing and listing.owner_id == user.id) or user.role == UserRole.admin:
        return True
    return bool(await select_rentals.count_roommates(db, rental.listing_id, user.id))


# ===========================================================================
# Rentals: CRUD
# ===========================================================================


@router.post("/rentals/", response_model=RentalOut, tags=["Rentals"])
async def create_rental(
    payload: RentalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rental:
    if payload.student_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Boshqa foydalanuvchi nomidan ijara yaratib bo'lmaydi")
    listing = await select_listings.get_by_id(db, payload.listing_id)
    if listing is None:
        raise HTTPException(404, "Listing topilmadi")
    rental = Rental(**payload.model_dump())
    await insert_rentals.create_rental(db, rental)
    await update_listings.decrement_available_spaces(db, listing)
    await db.commit()
    await db.refresh(rental)
    return rental


@router.post("/rentals/requests", response_model=RentalRequestOut, tags=["Rentals"])
async def create_rental_request(
    payload: RentalRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    listing = await select_listings.get_by_id(db, payload.listing_id)
    if listing is None or not listing.is_active:
        raise HTTPException(404, "Listing topilmadi")
    if listing.owner_id == current_user.id:
        raise HTTPException(400, "O'zingizning e'loningizni band qilib bo'lmaydi")
    if listing.available_spaces <= 0:
        raise HTTPException(400, "Bu kvartirada bo'sh joy qolmagan")

    active_rentals = await select_rentals.count_active_by_student(db, current_user.id)
    pending_requests = await select_rentals.count_pending_by_requester(db, current_user.id)
    if active_rentals + pending_requests >= 3:
        raise HTTPException(400, "Bitta student atigi 3 ta kvartirani band qilishi mumkin")
    if await select_rentals.get_pending_duplicate(db, listing.id, current_user.id) is not None:
        raise HTTPException(400, "Bu kvartira uchun so'rovingiz allaqachon yuborilgan")

    request = RentalRequest(
        listing_id=listing.id, requester_id=current_user.id,
        recipient_id=listing.owner_id, message=payload.message,
    )
    await insert_rentals.create_rental_request(db, request)
    if payload.message:
        await insert_rentals.create_request_message(
            db, RentalRequestMessage(request_id=request.id, sender_id=current_user.id, text=payload.message)
        )
    await _add_notification(
        db, user_id=listing.owner_id, actor_id=current_user.id,
        type=NotificationType.rental_request,
        title=f"{current_user.full_name} kvartirangizni band qilmoqchi",
        body=payload.message or "Yangi band qilish so'rovi keldi",
        request_id=request.id, listing_id=listing.id,
    )
    await db.commit()
    await db.refresh(request)
    return await _request_payload(db, request)


@router.get("/rentals/requests/me", response_model=list[RentalRequestOut], tags=["Rentals"])
async def get_my_rental_requests(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    requests = await select_rentals.get_requests_by_requester(db, current_user.id)
    return [await _request_payload(db, r) for r in requests]


@router.get("/rentals/conversations", tags=["Rentals"])
async def get_rental_conversations(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    requests = await select_rentals.get_conversations(db, current_user.id)
    return [await _conversation_payload(db, r, current_user) for r in requests]


@router.get("/rentals/requests/inbox", response_model=list[RentalRequestOut], tags=["Rentals"])
async def get_rental_request_inbox(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    requests = await select_rentals.get_requests_inbox(db, current_user.id)
    return [await _request_payload(db, r) for r in requests]


@router.get("/rentals/requests/{request_id}/messages", response_model=list[RentalRequestMessageOut], tags=["Rentals"])
async def get_rental_request_messages(request_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    request = await select_rentals.get_request_by_id(db, request_id)
    if request is None:
        raise HTTPException(404, "So'rov topilmadi")
    if not await _can_access_request(request, current_user):
        raise HTTPException(403, "Bu so'rovga kirish ruxsati yo'q")
    rows = await select_rentals.get_request_messages(db, request.id)
    return [{"id": m.id, "request_id": m.request_id, "sender_id": m.sender_id, "sender_name": s.full_name, "text": m.text, "created_at": m.created_at} for m, s in rows]


@router.post("/rentals/requests/{request_id}/messages", response_model=RentalRequestMessageOut, tags=["Rentals"])
async def send_rental_request_message(request_id: uuid.UUID, payload: RentalMessageCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    request = await select_rentals.get_request_by_id(db, request_id)
    if request is None:
        raise HTTPException(404, "So'rov topilmadi")
    if not await _can_access_request(request, current_user):
        raise HTTPException(403, "Bu so'rovga xabar yozish ruxsati yo'q")
    message = RentalRequestMessage(request_id=request.id, sender_id=current_user.id, text=payload.text)
    await insert_rentals.create_request_message(db, message)
    recipient_id = request.recipient_id if current_user.id == request.requester_id else request.requester_id
    await _add_notification(
        db, user_id=recipient_id, actor_id=current_user.id,
        type=NotificationType.system,
        title=f"{current_user.full_name} sizga xabar yozdi",
        body=payload.text, request_id=request.id, listing_id=request.listing_id,
    )
    await db.commit()
    await db.refresh(message)
    return {"id": message.id, "request_id": message.request_id, "sender_id": message.sender_id, "sender_name": current_user.full_name, "text": message.text, "created_at": message.created_at}


@router.patch("/rentals/requests/{request_id}/accept", response_model=RentalRequestOut, tags=["Rentals"])
async def accept_rental_request(request_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    request = await db.scalar(select(RentalRequest).where(RentalRequest.id == request_id).with_for_update())
    if request is None:
        raise HTTPException(404, "So'rov topilmadi")
    if request.recipient_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "So'rovni faqat e'lon egasi qabul qiladi")
    if request.status != RentalRequestStatus.pending:
        raise HTTPException(400, "Bu so'rov allaqachon ko'rib chiqilgan")
    listing = await db.scalar(select(Listing).where(Listing.id == request.listing_id).with_for_update())
    if listing is None:
        raise HTTPException(404, "Kvartira topilmadi")
    if listing.available_spaces <= 0:
        await update_rentals.reject_request(db, request)
        await _add_notification(db, user_id=request.requester_id, actor_id=current_user.id, type=NotificationType.rental_rejected, title="So'rovingiz avtomatik rad etildi", body="Bu kvartirada bo'sh joy qolmadi", request_id=request.id, listing_id=listing.id)
        await db.commit()
        await db.refresh(request)
        return await _request_payload(db, request)
    if not listing.is_active:
        raise HTTPException(400, "Bu kvartirada bo'sh joy qolmagan")

    rental = Rental(listing_id=listing.id, student_id=request.requester_id, start_date=date.today(), price_usd=listing.price_usd)
    await insert_rentals.create_rental(db, rental)
    await update_listings.decrement_available_spaces(db, listing)
    await update_rentals.accept_request(db, request, rental.id)

    accepted_user = await select_users.get_by_id(db, request.requester_id)
    accepted_user_name = accepted_user.full_name if accepted_user else "Foydalanuvchi"
    for other_request in await select_rentals.get_pending_by_requester_excluding(db, request.requester_id, request.id):
        await update_rentals.reject_request(db, other_request)
        await _add_notification(db, user_id=other_request.requester_id, actor_id=current_user.id, type=NotificationType.rental_rejected, title="Boshqa so'rovingiz avtomatik rad etildi", body="Siz bitta kvartiraga qabul qilinganingiz uchun qolgan band qilish so'rovlari yopildi", request_id=other_request.id, listing_id=other_request.listing_id)
        await _add_notification(db, user_id=other_request.recipient_id, actor_id=current_user.id, type=NotificationType.rental_rejected, title="Band qilish so'rovi avtomatik yopildi", body=f"{accepted_user_name} boshqa kvartiraga qabul qilindi", request_id=other_request.id, listing_id=other_request.listing_id)

    if listing.available_spaces == 0:
        for other_request in await select_rentals.get_pending_for_listing_excluding(db, listing.id, request.id):
            await update_rentals.reject_request(db, other_request)
            await _add_notification(db, user_id=other_request.requester_id, actor_id=current_user.id, type=NotificationType.rental_rejected, title="So'rovingiz avtomatik rad etildi", body="Bu kvartirada bo'sh joy qolmadi", request_id=other_request.id, listing_id=listing.id)

    await _add_notification(db, user_id=request.requester_id, actor_id=current_user.id, type=NotificationType.rental_accepted, title="So'rovingiz qabul qilindi", body="Kvartira My Room bo'limiga qo'shildi", request_id=request.id, listing_id=listing.id)
    await db.commit()
    await db.refresh(request)
    return await _request_payload(db, request)


@router.patch("/rentals/requests/{request_id}/reject", response_model=RentalRequestOut, tags=["Rentals"])
async def reject_rental_request(request_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    request = await select_rentals.get_request_by_id(db, request_id)
    if request is None:
        raise HTTPException(404, "So'rov topilmadi")
    if request.recipient_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "So'rovni faqat e'lon egasi rad qiladi")
    await update_rentals.reject_request(db, request)
    await _add_notification(db, user_id=request.requester_id, actor_id=current_user.id, type=NotificationType.rental_rejected, title="So'rovingiz rad etildi", body="Owner yoki broker band qilish so'rovingizni rad etdi", request_id=request.id, listing_id=request.listing_id)
    await db.commit()
    await db.refresh(request)
    return await _request_payload(db, request)


@router.get("/rentals/owner/me", response_model=list[OwnerRentalOut], tags=["Rentals"])
async def get_owner_rentals(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.owner, UserRole.admin, UserRole.makler]:
        raise HTTPException(403, "Owner ijaralariga kirish ruxsati yo'q")
    rentals = []
    for rental, listing, student in await select_rentals.get_owner_rental_rows(db, current_user.id):
        rentals.append({
            "id": rental.id, "listing_id": rental.listing_id,
            "student": {"id": student.id, "full_name": student.full_name, "phone": student.phone, "is_verified": student.is_verified},
            "listing": {"id": listing.id, "region": listing.region, "district": listing.district, "address": listing.address, "price_usd": listing.price_usd},
            "start_date": rental.start_date, "end_date": rental.end_date, "price_usd": rental.price_usd, "is_active": rental.is_active, "created_at": rental.created_at,
        })
    return rentals


@router.get("/rentals/user/{user_id}", response_model=list[RentalOut], tags=["Rentals"])
async def get_rentals_by_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Bu ijaralarga kirish ruxsati yo'q")
    return await select_rentals.get_by_student_id(db, user_id)


@router.get("/rentals/me/rooms", response_model=list[MyRoomOut], tags=["Rentals"])
async def get_my_rooms(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rooms = []
    for rental, listing, owner in await select_rentals.get_my_room_rows(db, current_user.id):
        neighbors = await select_rentals.get_neighbors(db, listing.id, current_user.id)
        next_date = _next_payment_date(rental.start_date)
        rooms.append({
            "id": rental.id, "listing_id": rental.listing_id,
            "listing": {"id": listing.id, "region": listing.region, "district": listing.district, "address": listing.address, "room_number": listing.room_number, "price_usd": listing.price_usd, "images": listing.images[:1] if listing.images else [], "available_spaces": listing.available_spaces, "max_guests": listing.max_guests},
            "owner": _user_payload(owner), "neighbors": [_user_payload(n) for n in neighbors],
            "start_date": rental.start_date, "end_date": rental.end_date, "price_usd": rental.price_usd,
            "is_active": rental.is_active, "next_payment_date": next_date, "payment_days_left": (next_date - date.today()).days, "created_at": rental.created_at,
        })
    return rooms


@router.get("/rentals/{rental_id}/room-messages", response_model=list[RoomMessageOut], tags=["Rentals"])
async def get_room_messages(rental_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None:
        raise HTTPException(404, "Rental topilmadi")
    if not await _can_access_rental(db, rental, current_user):
        raise HTTPException(403, "Room chatga kirish ruxsati yo'q")
    rows = await select_rentals.get_room_messages(db, rental.listing_id)
    return [{"id": m.id, "rental_id": m.rental_id, "listing_id": m.listing_id, "sender_id": m.sender_id, "sender_name": s.full_name, "text": m.text, "created_at": m.created_at} for m, s in rows]


@router.post("/rentals/{rental_id}/room-messages", response_model=RoomMessageOut, tags=["Rentals"])
async def send_room_message(rental_id: uuid.UUID, payload: RentalMessageCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None:
        raise HTTPException(404, "Rental topilmadi")
    if not await _can_access_rental(db, rental, current_user):
        raise HTTPException(403, "Room chatga yozish ruxsati yo'q")
    message = await insert_rentals.create_room_message(db, RoomMessage(rental_id=rental.id, listing_id=rental.listing_id, sender_id=current_user.id, text=payload.text))
    return {"id": message.id, "rental_id": message.rental_id, "listing_id": message.listing_id, "sender_id": message.sender_id, "sender_name": current_user.full_name, "text": message.text, "created_at": message.created_at}


@router.post("/rentals/{rental_id}/maintenance-reports", response_model=MaintenanceReportOut, tags=["Rentals"])
async def create_maintenance_report(rental_id: uuid.UUID, payload: MaintenanceReportCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None:
        raise HTTPException(404, "Rental topilmadi")
    listing = await select_listings.get_by_id(db, rental.listing_id)
    if rental.student_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Muammo xabarini faqat ijarachi yuboradi")
    return await insert_rentals.create_maintenance_report(
        db, MaintenanceReport(rental_id=rental.id, listing_id=rental.listing_id, reporter_id=current_user.id, recipient_id=listing.owner_id, text=payload.text, image_url=payload.image_url)
    )


@router.post("/rentals/{rental_id}/repost-vacancy", tags=["Rentals"])
async def repost_vacancy(rental_id: uuid.UUID, payload: VacancyRepostCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None or not rental.is_active:
        raise HTTPException(404, "Faol rental topilmadi")
    if rental.student_id != current_user.id:
        raise HTTPException(403, "Faqat shu xonada yashayotgan user reklama bera oladi")
    source_listing = await select_listings.get_by_id(db, rental.listing_id)
    if source_listing is None:
        raise HTTPException(404, "Listing topilmadi")
    if payload.available_spaces > max(source_listing.available_spaces, 1):
        raise HTTPException(400, "Bo'sh joy soni noto'g'ri")
    listing = Listing(owner_id=current_user.id, region=source_listing.region, district=source_listing.district, address=source_listing.address, building_number=source_listing.building_number, room_number=source_listing.room_number, floor=source_listing.floor, total_floors=source_listing.total_floors, latitude=source_listing.latitude, longitude=source_listing.longitude, rooms_count=source_listing.rooms_count, area_m2=source_listing.area_m2, price_usd=source_listing.price_usd, target_gender=source_listing.target_gender, source=ListingSource.exiting_student, max_guests=source_listing.max_guests, available_spaces=payload.available_spaces, amenities=source_listing.amenities or {}, images=source_listing.images or [], description=payload.description or source_listing.description, is_active=True)
    await insert_listings.create_listing(db, listing)
    listing = await insert_listings.commit_listing(db, listing)
    return {"success": True, "listing_id": str(listing.id), "message": "Birinchi vacancy reklamasi bepul joylandi"}


@router.patch("/rentals/{rental_id}/close", response_model=RentalOut, tags=["Rentals"])
async def close_rental(rental_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None:
        raise HTTPException(404, "Rental topilmadi")
    listing = await select_listings.get_by_id(db, rental.listing_id)
    is_owner = listing is not None and listing.owner_id == current_user.id
    is_tenant = rental.student_id == current_user.id
    if not (is_owner or is_tenant or current_user.role == UserRole.admin):
        raise HTTPException(403, "Bu ijarani yopishga ruxsat yo'q")
    rental.is_active = False
    if listing is not None:
        await update_listings.increment_available_spaces(db, listing)
    await db.commit()
    await db.refresh(rental)
    return rental


# ===========================================================================
# Payments
# ===========================================================================


@router.post("/payments/", response_model=PaymentOut, tags=["Payments"])
async def create_payment(payload: PaymentCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Payment:
    if payload.payer_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Boshqa foydalanuvchi nomidan to'lov yaratib bo'lmaydi")
    payment = Payment(**payload.model_dump())
    return await insert_payments.create(db, payment)


@router.get("/payments/", response_model=list[PaymentOut], tags=["Payments"])
async def list_payments(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await select_payments.list_by_payer(db, current_user.id, skip=skip, limit=limit)


@router.get("/payments/user/{user_id}", response_model=list[PaymentOut], tags=["Payments"])
async def get_user_payments(user_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Bu tolovlarga kirish ruxsati yo'q")
    return await select_payments.get_by_payer_id(db, user_id)


@router.get("/payments/{payment_id}", response_model=PaymentOut, tags=["Payments"])
async def get_payment(payment_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    payment = await select_payments.get_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(404, "Tolov topilmadi")
    if payment.payer_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Bu tolovga kirish ruxsati yo'q")
    return payment


@router.patch("/payments/{payment_id}/status", response_model=PaymentOut, tags=["Payments"])
async def update_payment_status(payment_id: uuid.UUID, payload: PaymentStatusUpdate, current_user: User = Depends(require_roles("admin", "makler")), db: AsyncSession = Depends(get_db)):
    payment = await select_payments.get_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(404, "Tolov topilmadi")
    updated = await update_payments.update_status(db, payment_id, payload.status)
    if updated is None:
        raise HTTPException(404, "Tolov topilmadi")
    return updated


@router.patch("/payments/{payment_id}", response_model=PaymentOut, tags=["Payments"])
async def edit_payment(payment_id: uuid.UUID, payload: PaymentUpdate, current_user: User = Depends(require_roles("admin", "makler")), db: AsyncSession = Depends(get_db)):
    payment = await select_payments.get_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(404, "Tolov topilmadi")
    updated = await update_payments.update_fields(db, payment_id, amount=payload.amount, billing_month=payload.billing_month, status=payload.status)
    if updated is None:
        raise HTTPException(404, "Tolov topilmadi")
    return updated


@router.delete("/payments/{payment_id}", tags=["Payments"])
async def delete_payment(payment_id: uuid.UUID, current_user: User = Depends(require_roles("admin", "makler")), db: AsyncSession = Depends(get_db)):
    payment = await select_payments.get_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(404, "Tolov topilmadi")
    await delete_payments.delete_by_id(db, payment_id)
    return {"message": "Tolov muvaffaqiyatli o'chirildi", "payment_id": str(payment_id)}


# ===========================================================================
# Reviews
# ===========================================================================


@router.post("/reviews/", response_model=ReviewOut, tags=["Reviews"])
async def create_review(payload: ReviewCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> Review:
    listing = await select_listings.get_by_id(db, payload.listing_id)
    if listing is None:
        raise HTTPException(404, "Listing topilmadi")
    existing = await select_reviews.get_by_listing_and_author(db, payload.listing_id, current_user.id)
    if existing is not None:
        raise HTTPException(400, "Bu listing uchun sharh qoldirgansiz")
    review = Review(listing_id=payload.listing_id, author_id=current_user.id, rating=payload.rating, review_text=payload.review_text)
    created = await insert_reviews.create(db, review)
    if created is None:
        raise HTTPException(500, "Sharh yaratildi, lekin qayta yuklanmadi")
    return created


@router.get("/reviews/listing/{listing_id}", response_model=list[ReviewOut], tags=["Reviews"])
async def get_reviews_by_listing(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[Review]:
    return await select_reviews.get_by_listing_with_author(db, listing_id)


# ===========================================================================
# Subscriptions
# ===========================================================================


@router.get("/subscriptions/me", response_model=list[SubscriptionOut], tags=["Subscriptions"])
async def get_my_subscriptions(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await select_subscriptions.get_my_subscriptions(db, current_user.id)


@router.post("/subscriptions/purchase", response_model=SubscriptionOut, tags=["Subscriptions"])
async def purchase_subscription(payload: SubscriptionPurchase, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    subscription = Subscription(user_id=current_user.id, **payload.model_dump())
    return await insert_subscriptions.create(db, subscription)


@router.post("/subscriptions/{plan_id}", response_model=SubscriptionOut, tags=["Subscriptions"])
async def purchase_subscription_by_plan(plan_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    plans = {"free": (SubscriptionType.makler_s, 5, 30), "s": (SubscriptionType.makler_s, 25, 30), "l": (SubscriptionType.makler_l, 100, 30)}
    if plan_id not in plans:
        raise HTTPException(404, "Plan topilmadi")
    sub_type, limit, days = plans[plan_id]
    today = date.today()
    from datetime import timedelta
    subscription = Subscription(user_id=current_user.id, type=sub_type, start_date=today, end_date=today + timedelta(days=days), listing_limit=limit)
    return await insert_subscriptions.create(db, subscription)


@router.patch("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionOut, tags=["Subscriptions"])
async def cancel_subscription(subscription_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    subscription = await select_subscriptions.get_by_id(db, subscription_id)
    if subscription is None:
        raise HTTPException(404, "Subscription topilmadi")
    if subscription.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Bu subscriptionni bekor qilishga ruxsat yo'q")
    updated = await update_subscriptions.deactivate(db, subscription_id)
    if updated is None:
        raise HTTPException(404, "Subscription topilmadi")
    return updated
