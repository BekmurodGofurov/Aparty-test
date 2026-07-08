import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.listing import Listing, ListingSource
from app.models.notification import Notification, NotificationType
from app.models.rental import (
    MaintenanceReport,
    Rental,
    RentalRequest,
    RentalRequestMessage,
    RentalRequestStatus,
    RoomMessage,
)
from app.models.user import User, UserRole
from app.schemas.rental import (
    MaintenanceReportCreate,
    MaintenanceReportOut,
    MyRoomOut,
    OwnerRentalOut,
    RentalCreate,
    RentalMessageCreate,
    RentalOut,
    RentalRequestCreate,
    RentalRequestMessageOut,
    RentalRequestOut,
    RoomMessageOut,
    VacancyRepostCreate,
)
from database.operations.insert import listings as insert_listings
from database.operations.insert import rentals as insert_rentals
from database.operations.select import listings as select_listings
from database.operations.select import rentals as select_rentals
from database.operations.select import users as select_users
from database.operations.update import listings as update_listings
from database.operations.update import rentals as update_rentals

router = APIRouter()


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "is_verified": user.is_verified,
    }


def _listing_payload(listing: Listing) -> dict:
    return {
        "id": listing.id,
        "region": listing.region,
        "district": listing.district,
        "address": listing.address,
        "price_usd": listing.price_usd,
        "images": listing.images[:1] if listing.images else [],
    }


def _next_payment_date(start_date: date) -> date:
    today = date.today()
    month = today.month
    year = today.year
    day = min(start_date.day, 28)
    next_date = date(year, month, day)
    if next_date < today:
        month += 1
        if month > 12:
            month = 1
            year += 1
        next_date = date(year, month, day)
    return next_date


def _notification_target(request_id) -> str:
    return f"/messages?request={request_id}"


async def _add_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    type: NotificationType,
    title: str,
    body: str | None = None,
    request_id=None,
    listing_id=None,
) -> None:
    await insert_rentals.create_notification(
        db,
        Notification(
            user_id=user_id,
            actor_id=actor_id,
            type=type,
            title=title,
            body=body,
            request_id=request_id,
            listing_id=listing_id,
            target_url=_notification_target(request_id) if request_id else "/messages",
        ),
    )


async def _request_payload(db: AsyncSession, request: RentalRequest) -> dict:
    listing = await select_listings.get_by_id(db, request.listing_id)
    requester = await select_users.get_by_id(db, request.requester_id)
    recipient = await select_users.get_by_id(db, request.recipient_id)
    return {
        "id": request.id,
        "listing_id": request.listing_id,
        "requester": _user_payload(requester),
        "recipient": _user_payload(recipient),
        "listing": _listing_payload(listing),
        "status": request.status,
        "message": request.message,
        "rental_id": request.rental_id,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
    }


async def _conversation_payload(db: AsyncSession, request: RentalRequest, current_user: User) -> dict:
    payload = await _request_payload(db, request)
    rows = await select_rentals.get_request_messages(db, request.id)
    messages = [
        {
            "id": message.id,
            "request_id": message.request_id,
            "sender_id": message.sender_id,
            "sender_name": sender.full_name,
            "text": message.text,
            "created_at": message.created_at,
        }
        for message, sender in rows
    ]
    other = payload["recipient"] if request.requester_id == current_user.id else payload["requester"]
    return {
        **payload,
        "other_user": other,
        "messages": messages,
        "last_message": messages[-1] if messages else None,
    }


async def _can_access_request(request: RentalRequest, user: User) -> bool:
    is_party = user.id in {request.requester_id, request.recipient_id}
    is_admin = user.role == UserRole.admin
    return is_party or is_admin


async def _can_access_rental(db: AsyncSession, rental: Rental, user: User) -> bool:
    listing = await select_listings.get_by_id(db, rental.listing_id)
    is_tenant = rental.student_id == user.id
    is_owner = listing is not None and listing.owner_id == user.id
    is_admin = user.role == UserRole.admin
    if is_tenant or is_owner or is_admin:
        return True
    roommate_count = await select_rentals.count_roommates(db, rental.listing_id, user.id)
    return bool(roommate_count)


@router.post("/", response_model=RentalOut)
async def create_rental(
    payload: RentalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rental:
    if payload.student_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Boshqa foydalanuvchi nomidan ijara yaratib bo'lmaydi")
    listing = await select_listings.get_by_id(db, payload.listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    rental = Rental(**payload.model_dump())
    await insert_rentals.create_rental(db, rental)
    await update_listings.decrement_available_spaces(db, listing)
    await db.commit()
    await db.refresh(rental)
    return rental


@router.post("/requests", response_model=RentalRequestOut)
async def create_rental_request(
    payload: RentalRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    listing = await select_listings.get_by_id(db, payload.listing_id)
    if listing is None or not listing.is_active:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="O'zingizning e'loningizni band qilib bo'lmaydi")
    if listing.available_spaces <= 0:
        raise HTTPException(status_code=400, detail="Bu kvartirada bo'sh joy qolmagan")

    active_rentals = await select_rentals.count_active_by_student(db, current_user.id)
    pending_requests = await select_rentals.count_pending_by_requester(db, current_user.id)
    if active_rentals + pending_requests >= 3:
        raise HTTPException(status_code=400, detail="Bitta student atigi 3 ta kvartirani band qilishi mumkin")

    if await select_rentals.get_pending_duplicate(db, listing.id, current_user.id) is not None:
        raise HTTPException(status_code=400, detail="Bu kvartira uchun so'rovingiz allaqachon yuborilgan")

    request = RentalRequest(
        listing_id=listing.id,
        requester_id=current_user.id,
        recipient_id=listing.owner_id,
        message=payload.message,
    )
    await insert_rentals.create_rental_request(db, request)
    if payload.message:
        await insert_rentals.create_request_message(
            db,
            RentalRequestMessage(request_id=request.id, sender_id=current_user.id, text=payload.message),
        )
    await _add_notification(
        db,
        user_id=listing.owner_id,
        actor_id=current_user.id,
        type=NotificationType.rental_request,
        title=f"{current_user.full_name} kvartirangizni band qilmoqchi",
        body=payload.message or "Yangi band qilish so'rovi keldi",
        request_id=request.id,
        listing_id=listing.id,
    )
    await db.commit()
    await db.refresh(request)
    return await _request_payload(db, request)


@router.get("/requests/me", response_model=list[RentalRequestOut])
async def get_my_rental_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    requests = await select_rentals.get_requests_by_requester(db, current_user.id)
    return [await _request_payload(db, request) for request in requests]


@router.get("/conversations")
async def get_rental_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    requests = await select_rentals.get_conversations(db, current_user.id)
    return [await _conversation_payload(db, request, current_user) for request in requests]


@router.get("/requests/inbox", response_model=list[RentalRequestOut])
async def get_rental_request_inbox(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    requests = await select_rentals.get_requests_inbox(db, current_user.id)
    return [await _request_payload(db, request) for request in requests]


@router.get("/requests/{request_id}/messages", response_model=list[RentalRequestMessageOut])
async def get_rental_request_messages(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    request = await select_rentals.get_request_by_id(db, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if not await _can_access_request(request, current_user):
        raise HTTPException(status_code=403, detail="Bu so'rovga kirish ruxsati yo'q")

    rows = await select_rentals.get_request_messages(db, request.id)
    return [
        {
            "id": message.id,
            "request_id": message.request_id,
            "sender_id": message.sender_id,
            "sender_name": sender.full_name,
            "text": message.text,
            "created_at": message.created_at,
        }
        for message, sender in rows
    ]


@router.post("/requests/{request_id}/messages", response_model=RentalRequestMessageOut)
async def send_rental_request_message(
    request_id: uuid.UUID,
    payload: RentalMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    request = await select_rentals.get_request_by_id(db, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if not await _can_access_request(request, current_user):
        raise HTTPException(status_code=403, detail="Bu so'rovga xabar yozish ruxsati yo'q")

    message = RentalRequestMessage(request_id=request.id, sender_id=current_user.id, text=payload.text)
    await insert_rentals.create_request_message(db, message)
    recipient_id = request.recipient_id if current_user.id == request.requester_id else request.requester_id
    await _add_notification(
        db,
        user_id=recipient_id,
        actor_id=current_user.id,
        type=NotificationType.request_message,
        title=f"{current_user.full_name} sizga xabar yozdi",
        body=payload.text,
        request_id=request.id,
        listing_id=request.listing_id,
    )
    await db.commit()
    await db.refresh(message)
    return {
        "id": message.id,
        "request_id": message.request_id,
        "sender_id": message.sender_id,
        "sender_name": current_user.full_name,
        "text": message.text,
        "created_at": message.created_at,
    }


@router.patch("/requests/{request_id}/accept", response_model=RentalRequestOut)
async def accept_rental_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    request = await select_rentals.get_request_by_id(db, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if request.recipient_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="So'rovni faqat e'lon egasi qabul qiladi")
    if request.status != RentalRequestStatus.pending:
        raise HTTPException(status_code=400, detail="Bu so'rov allaqachon ko'rib chiqilgan")

    listing = await select_listings.get_by_id(db, request.listing_id)
    if listing is None or listing.available_spaces <= 0:
        raise HTTPException(status_code=400, detail="Bu kvartirada bo'sh joy qolmagan")

    rental = Rental(
        listing_id=listing.id,
        student_id=request.requester_id,
        start_date=date.today(),
        price_usd=listing.price_usd,
    )
    await insert_rentals.create_rental(db, rental)
    await update_listings.decrement_available_spaces(db, listing)
    await update_rentals.accept_request(db, request, rental.id)

    accepted_user = await select_users.get_by_id(db, request.requester_id)
    accepted_user_name = accepted_user.full_name if accepted_user else "Foydalanuvchi"
    other_user_requests = await select_rentals.get_pending_by_requester_excluding(
        db, request.requester_id, request.id
    )
    for other_request in other_user_requests:
        await update_rentals.reject_request(db, other_request)
        await _add_notification(
            db,
            user_id=other_request.requester_id,
            actor_id=current_user.id,
            type=NotificationType.request_rejected,
            title="Boshqa so'rovingiz avtomatik rad etildi",
            body="Siz bitta kvartiraga qabul qilinganingiz uchun qolgan band qilish so'rovlari yopildi",
            request_id=other_request.id,
            listing_id=other_request.listing_id,
        )
        await _add_notification(
            db,
            user_id=other_request.recipient_id,
            actor_id=current_user.id,
            type=NotificationType.request_rejected,
            title="Band qilish so'rovi avtomatik yopildi",
            body=f"{accepted_user_name} boshqa kvartiraga qabul qilindi",
            request_id=other_request.id,
            listing_id=other_request.listing_id,
        )

    if listing.available_spaces == 0:
        same_listing_requests = await select_rentals.get_pending_for_listing_excluding(
            db, listing.id, request.id
        )
        for other_request in same_listing_requests:
            await update_rentals.reject_request(db, other_request)
            await _add_notification(
                db,
                user_id=other_request.requester_id,
                actor_id=current_user.id,
                type=NotificationType.request_rejected,
                title="So'rovingiz avtomatik rad etildi",
                body="Bu kvartirada bo'sh joy qolmadi",
                request_id=other_request.id,
                listing_id=listing.id,
            )

    await _add_notification(
        db,
        user_id=request.requester_id,
        actor_id=current_user.id,
        type=NotificationType.request_accepted,
        title="So'rovingiz qabul qilindi",
        body="Kvartira My Room bo'limiga qo'shildi",
        request_id=request.id,
        listing_id=listing.id,
    )
    await db.commit()
    await db.refresh(request)
    return await _request_payload(db, request)


@router.patch("/requests/{request_id}/reject", response_model=RentalRequestOut)
async def reject_rental_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    request = await select_rentals.get_request_by_id(db, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if request.recipient_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="So'rovni faqat e'lon egasi rad qiladi")
    await update_rentals.reject_request(db, request)
    await _add_notification(
        db,
        user_id=request.requester_id,
        actor_id=current_user.id,
        type=NotificationType.request_rejected,
        title="So'rovingiz rad etildi",
        body="Owner yoki broker band qilish so'rovingizni rad etdi",
        request_id=request.id,
        listing_id=request.listing_id,
    )
    await db.commit()
    await db.refresh(request)
    return await _request_payload(db, request)


@router.get("/owner/me", response_model=list[OwnerRentalOut])
async def get_owner_rentals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    if current_user.role not in [UserRole.owner, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Owner ijaralariga kirish ruxsati yo'q")

    rentals: list[dict] = []
    for rental, listing, student in await select_rentals.get_owner_rental_rows(db, current_user.id):
        rentals.append(
            {
                "id": rental.id,
                "listing_id": rental.listing_id,
                "student": {
                    "id": student.id,
                    "full_name": student.full_name,
                    "phone": student.phone,
                    "is_verified": student.is_verified,
                },
                "listing": {
                    "id": listing.id,
                    "region": listing.region,
                    "district": listing.district,
                    "address": listing.address,
                    "price_usd": listing.price_usd,
                },
                "start_date": rental.start_date,
                "end_date": rental.end_date,
                "price_usd": rental.price_usd,
                "is_active": rental.is_active,
                "created_at": rental.created_at,
            }
        )
    return rentals


@router.get("/user/{user_id}", response_model=list[RentalOut])
async def get_rentals_by_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Rental]:
    if user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Bu ijaralarga kirish ruxsati yo'q")
    return await select_rentals.get_by_student_id(db, user_id)


@router.get("/me/rooms", response_model=list[MyRoomOut])
async def get_my_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    rooms = []
    for rental, listing, owner in await select_rentals.get_my_room_rows(db, current_user.id):
        neighbors = await select_rentals.get_neighbors(db, listing.id, current_user.id)
        next_date = _next_payment_date(rental.start_date)
        rooms.append(
            {
                "id": rental.id,
                "listing_id": rental.listing_id,
                "listing": {
                    "id": listing.id,
                    "region": listing.region,
                    "district": listing.district,
                    "address": listing.address,
                    "room_number": listing.room_number,
                    "price_usd": listing.price_usd,
                    "images": listing.images[:1] if listing.images else [],
                    "available_spaces": listing.available_spaces,
                    "max_guests": listing.max_guests,
                },
                "owner": _user_payload(owner),
                "neighbors": [_user_payload(neighbor) for neighbor in neighbors],
                "start_date": rental.start_date,
                "end_date": rental.end_date,
                "price_usd": rental.price_usd,
                "is_active": rental.is_active,
                "next_payment_date": next_date,
                "payment_days_left": (next_date - date.today()).days,
                "created_at": rental.created_at,
            }
        )
    return rooms


@router.get("/{rental_id}/room-messages", response_model=list[RoomMessageOut])
async def get_room_messages(
    rental_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental topilmadi")
    if not await _can_access_rental(db, rental, current_user):
        raise HTTPException(status_code=403, detail="Room chatga kirish ruxsati yo'q")

    rows = await select_rentals.get_room_messages(db, rental.listing_id)
    return [
        {
            "id": message.id,
            "rental_id": message.rental_id,
            "listing_id": message.listing_id,
            "sender_id": message.sender_id,
            "sender_name": sender.full_name,
            "text": message.text,
            "created_at": message.created_at,
        }
        for message, sender in rows
    ]


@router.post("/{rental_id}/room-messages", response_model=RoomMessageOut)
async def send_room_message(
    rental_id: uuid.UUID,
    payload: RentalMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental topilmadi")
    if not await _can_access_rental(db, rental, current_user):
        raise HTTPException(status_code=403, detail="Room chatga yozish ruxsati yo'q")

    message = await insert_rentals.create_room_message(
        db,
        RoomMessage(
            rental_id=rental.id,
            listing_id=rental.listing_id,
            sender_id=current_user.id,
            text=payload.text,
        ),
    )
    return {
        "id": message.id,
        "rental_id": message.rental_id,
        "listing_id": message.listing_id,
        "sender_id": message.sender_id,
        "sender_name": current_user.full_name,
        "text": message.text,
        "created_at": message.created_at,
    }


@router.post("/{rental_id}/maintenance-reports", response_model=MaintenanceReportOut)
async def create_maintenance_report(
    rental_id: uuid.UUID,
    payload: MaintenanceReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaintenanceReport:
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental topilmadi")
    listing = await select_listings.get_by_id(db, rental.listing_id)
    if rental.student_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Muammo xabarini faqat ijarachi yuboradi")
    return await insert_rentals.create_maintenance_report(
        db,
        MaintenanceReport(
            rental_id=rental.id,
            listing_id=rental.listing_id,
            reporter_id=current_user.id,
            recipient_id=listing.owner_id,
            text=payload.text,
            image_url=payload.image_url,
        ),
    )


@router.post("/{rental_id}/repost-vacancy")
async def repost_vacancy(
    rental_id: uuid.UUID,
    payload: VacancyRepostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None or not rental.is_active:
        raise HTTPException(status_code=404, detail="Faol rental topilmadi")
    if rental.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Faqat shu xonada yashayotgan user reklama bera oladi")
    source_listing = await select_listings.get_by_id(db, rental.listing_id)
    if source_listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if payload.available_spaces > max(source_listing.available_spaces, 1):
        raise HTTPException(status_code=400, detail="Bo'sh joy soni noto'g'ri")

    listing = Listing(
        owner_id=current_user.id,
        region=source_listing.region,
        district=source_listing.district,
        address=source_listing.address,
        building_number=source_listing.building_number,
        room_number=source_listing.room_number,
        floor=source_listing.floor,
        total_floors=source_listing.total_floors,
        latitude=source_listing.latitude,
        longitude=source_listing.longitude,
        rooms_count=source_listing.rooms_count,
        area_m2=source_listing.area_m2,
        price_usd=source_listing.price_usd,
        target_gender=source_listing.target_gender,
        source=ListingSource.exiting_student,
        max_guests=source_listing.max_guests,
        available_spaces=payload.available_spaces,
        amenities=source_listing.amenities or {},
        images=source_listing.images or [],
        description=payload.description or source_listing.description,
        is_active=True,
    )
    await insert_listings.create_listing(db, listing)
    listing = await insert_listings.commit_listing(db, listing)
    return {"success": True, "listing_id": str(listing.id), "message": "Birinchi vacancy reklamasi bepul joylandi"}


@router.patch("/{rental_id}/close", response_model=RentalOut)
async def close_rental(
    rental_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rental:
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental topilmadi")
    listing = await select_listings.get_by_id(db, rental.listing_id)
    is_owner = listing is not None and listing.owner_id == current_user.id
    is_tenant = rental.student_id == current_user.id
    is_admin = current_user.role == UserRole.admin
    if not (is_owner or is_tenant or is_admin):
        raise HTTPException(status_code=403, detail="Bu ijarani yopishga ruxsat yo'q")
    rental.is_active = False
    if listing is not None:
        await update_listings.increment_available_spaces(db, listing)
    await db.commit()
    await db.refresh(rental)
    return rental
