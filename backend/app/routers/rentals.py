import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
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


def _add_notification(
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
    db.add(
        Notification(
            user_id=user_id,
            actor_id=actor_id,
            type=type,
            title=title,
            body=body,
            request_id=request_id,
            listing_id=listing_id,
            target_url=_notification_target(request_id) if request_id else "/messages",
        )
    )


async def _request_payload(db: AsyncSession, request: RentalRequest) -> dict:
    listing = await db.get(Listing, request.listing_id)
    requester = await db.get(User, request.requester_id)
    recipient = await db.get(User, request.recipient_id)
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
    rows = await db.execute(
        select(RentalRequestMessage, User)
        .join(User, RentalRequestMessage.sender_id == User.id)
        .where(RentalRequestMessage.request_id == request.id)
        .order_by(RentalRequestMessage.created_at)
    )
    messages = [
        {
            "id": message.id,
            "request_id": message.request_id,
            "sender_id": message.sender_id,
            "sender_name": sender.full_name,
            "text": message.text,
            "created_at": message.created_at,
        }
        for message, sender in rows.all()
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
    listing = await db.get(Listing, rental.listing_id)
    is_tenant = rental.student_id == user.id
    is_owner = listing is not None and listing.owner_id == user.id
    is_admin = user.role == UserRole.admin
    if is_tenant or is_owner or is_admin:
        return True
    roommate_count = await db.scalar(
        select(func.count(Rental.id)).where(
            Rental.listing_id == rental.listing_id,
            Rental.student_id == user.id,
            Rental.is_active.is_(True),
        )
    )
    return bool(roommate_count)


@router.post("/", response_model=RentalOut)
async def create_rental(
    payload: RentalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rental:
    if payload.student_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Boshqa foydalanuvchi nomidan ijara yaratib bo'lmaydi")
    listing = await db.get(Listing, payload.listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    rental = Rental(**payload.model_dump())
    db.add(rental)
    listing.available_spaces = max(0, listing.available_spaces - 1)
    if listing.available_spaces == 0:
        listing.is_active = False
    await db.commit()
    await db.refresh(rental)
    return rental


@router.post("/requests", response_model=RentalRequestOut)
async def create_rental_request(
    payload: RentalRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    listing = await db.get(Listing, payload.listing_id)
    if listing is None or not listing.is_active:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="O'zingizning e'loningizni band qilib bo'lmaydi")
    if listing.available_spaces <= 0:
        raise HTTPException(status_code=400, detail="Bu kvartirada bo'sh joy qolmagan")

    active_rentals = await db.scalar(
        select(func.count(Rental.id)).where(
            Rental.student_id == current_user.id,
            Rental.is_active.is_(True),
        )
    )
    pending_requests = await db.scalar(
        select(func.count(RentalRequest.id)).where(
            RentalRequest.requester_id == current_user.id,
            RentalRequest.status == RentalRequestStatus.pending,
        )
    )
    if (active_rentals or 0) + (pending_requests or 0) >= 3:
        raise HTTPException(status_code=400, detail="Bitta student atigi 3 ta kvartirani band qilishi mumkin")

    duplicate = await db.scalar(
        select(RentalRequest).where(
            RentalRequest.listing_id == listing.id,
            RentalRequest.requester_id == current_user.id,
            RentalRequest.status == RentalRequestStatus.pending,
        )
    )
    if duplicate is not None:
        raise HTTPException(status_code=400, detail="Bu kvartira uchun so'rovingiz allaqachon yuborilgan")

    request = RentalRequest(
        listing_id=listing.id,
        requester_id=current_user.id,
        recipient_id=listing.owner_id,
        message=payload.message,
    )
    db.add(request)
    if payload.message:
        await db.flush()
        db.add(RentalRequestMessage(request_id=request.id, sender_id=current_user.id, text=payload.message))
    await db.flush()
    _add_notification(
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
    rows = await db.execute(
        select(RentalRequest)
        .where(RentalRequest.requester_id == current_user.id)
        .order_by(desc(RentalRequest.created_at))
    )
    return [await _request_payload(db, request) for request in rows.scalars().all()]


@router.get("/conversations")
async def get_rental_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    rows = await db.execute(
        select(RentalRequest)
        .where(
            (RentalRequest.requester_id == current_user.id)
            | (RentalRequest.recipient_id == current_user.id)
        )
        .order_by(desc(RentalRequest.updated_at), desc(RentalRequest.created_at))
    )
    return [await _conversation_payload(db, request, current_user) for request in rows.scalars().all()]


@router.get("/requests/inbox", response_model=list[RentalRequestOut])
async def get_rental_request_inbox(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    rows = await db.execute(
        select(RentalRequest)
        .where(RentalRequest.recipient_id == current_user.id)
        .order_by(desc(RentalRequest.status == RentalRequestStatus.pending), desc(RentalRequest.created_at))
    )
    return [await _request_payload(db, request) for request in rows.scalars().all()]


@router.get("/requests/{request_id}/messages", response_model=list[RentalRequestMessageOut])
async def get_rental_request_messages(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    request = await db.get(RentalRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if not await _can_access_request(request, current_user):
        raise HTTPException(status_code=403, detail="Bu so'rovga kirish ruxsati yo'q")

    rows = await db.execute(
        select(RentalRequestMessage, User)
        .join(User, RentalRequestMessage.sender_id == User.id)
        .where(RentalRequestMessage.request_id == request.id)
        .order_by(RentalRequestMessage.created_at)
    )
    return [
        {
            "id": message.id,
            "request_id": message.request_id,
            "sender_id": message.sender_id,
            "sender_name": sender.full_name,
            "text": message.text,
            "created_at": message.created_at,
        }
        for message, sender in rows.all()
    ]


@router.post("/requests/{request_id}/messages", response_model=RentalRequestMessageOut)
async def send_rental_request_message(
    request_id: uuid.UUID,
    payload: RentalMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    request = await db.get(RentalRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if not await _can_access_request(request, current_user):
        raise HTTPException(status_code=403, detail="Bu so'rovga xabar yozish ruxsati yo'q")

    message = RentalRequestMessage(request_id=request.id, sender_id=current_user.id, text=payload.text)
    db.add(message)
    recipient_id = request.recipient_id if current_user.id == request.requester_id else request.requester_id
    _add_notification(
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
    request = await db.get(RentalRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if request.recipient_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="So'rovni faqat e'lon egasi qabul qiladi")
    if request.status != RentalRequestStatus.pending:
        raise HTTPException(status_code=400, detail="Bu so'rov allaqachon ko'rib chiqilgan")

    listing = await db.get(Listing, request.listing_id)
    if listing is None or listing.available_spaces <= 0:
        raise HTTPException(status_code=400, detail="Bu kvartirada bo'sh joy qolmagan")

    rental = Rental(
        listing_id=listing.id,
        student_id=request.requester_id,
        start_date=date.today(),
        price_usd=listing.price_usd,
    )
    db.add(rental)
    await db.flush()
    listing.available_spaces = max(0, listing.available_spaces - 1)
    if listing.available_spaces == 0:
        listing.is_active = False
    request.status = RentalRequestStatus.accepted
    request.rental_id = rental.id

    accepted_user = await db.get(User, request.requester_id)
    accepted_user_name = accepted_user.full_name if accepted_user else "Foydalanuvchi"
    other_user_requests = await db.execute(
        select(RentalRequest).where(
            RentalRequest.requester_id == request.requester_id,
            RentalRequest.id != request.id,
            RentalRequest.status == RentalRequestStatus.pending,
        )
    )
    for other_request in other_user_requests.scalars().all():
        other_request.status = RentalRequestStatus.rejected
        _add_notification(
            db,
            user_id=other_request.requester_id,
            actor_id=current_user.id,
            type=NotificationType.request_rejected,
            title="Boshqa so'rovingiz avtomatik rad etildi",
            body="Siz bitta kvartiraga qabul qilinganingiz uchun qolgan band qilish so'rovlari yopildi",
            request_id=other_request.id,
            listing_id=other_request.listing_id,
        )
        _add_notification(
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
        same_listing_requests = await db.execute(
            select(RentalRequest).where(
                RentalRequest.listing_id == listing.id,
                RentalRequest.id != request.id,
                RentalRequest.status == RentalRequestStatus.pending,
            )
        )
        for other_request in same_listing_requests.scalars().all():
            other_request.status = RentalRequestStatus.rejected
            _add_notification(
                db,
                user_id=other_request.requester_id,
                actor_id=current_user.id,
                type=NotificationType.request_rejected,
                title="So'rovingiz avtomatik rad etildi",
                body="Bu kvartirada bo'sh joy qolmadi",
                request_id=other_request.id,
                listing_id=listing.id,
            )

    _add_notification(
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
    request = await db.get(RentalRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if request.recipient_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="So'rovni faqat e'lon egasi rad qiladi")
    request.status = RentalRequestStatus.rejected
    _add_notification(
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

    result = await db.execute(
        select(Rental, Listing, User)
        .join(Listing, Rental.listing_id == Listing.id)
        .join(User, Rental.student_id == User.id)
        .where(Listing.owner_id == current_user.id)
        .order_by(desc(Rental.is_active), desc(Rental.created_at))
    )

    rentals: list[dict] = []
    for rental, listing, student in result.all():
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
    result = await db.execute(select(Rental).where(Rental.student_id == user_id).order_by(Rental.created_at.desc()))
    return list(result.scalars().all())


@router.get("/me/rooms", response_model=list[MyRoomOut])
async def get_my_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    rows = await db.execute(
        select(Rental, Listing, User)
        .join(Listing, Rental.listing_id == Listing.id)
        .join(User, Listing.owner_id == User.id)
        .where(Rental.student_id == current_user.id, Rental.is_active.is_(True))
        .order_by(desc(Rental.created_at))
    )
    rooms = []
    for rental, listing, owner in rows.all():
        neighbors_result = await db.execute(
            select(User)
            .join(Rental, Rental.student_id == User.id)
            .where(
                Rental.listing_id == listing.id,
                Rental.is_active.is_(True),
                User.id != current_user.id,
            )
            .order_by(User.full_name)
        )
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
                "neighbors": [_user_payload(neighbor) for neighbor in neighbors_result.scalars().all()],
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
    rental = await db.get(Rental, rental_id)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental topilmadi")
    if not await _can_access_rental(db, rental, current_user):
        raise HTTPException(status_code=403, detail="Room chatga kirish ruxsati yo'q")

    rows = await db.execute(
        select(RoomMessage, User)
        .join(User, RoomMessage.sender_id == User.id)
        .where(RoomMessage.listing_id == rental.listing_id)
        .order_by(RoomMessage.created_at)
    )
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
        for message, sender in rows.all()
    ]


@router.post("/{rental_id}/room-messages", response_model=RoomMessageOut)
async def send_room_message(
    rental_id: uuid.UUID,
    payload: RentalMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    rental = await db.get(Rental, rental_id)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental topilmadi")
    if not await _can_access_rental(db, rental, current_user):
        raise HTTPException(status_code=403, detail="Room chatga yozish ruxsati yo'q")

    message = RoomMessage(
        rental_id=rental.id,
        listing_id=rental.listing_id,
        sender_id=current_user.id,
        text=payload.text,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
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
    rental = await db.get(Rental, rental_id)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental topilmadi")
    listing = await db.get(Listing, rental.listing_id)
    if rental.student_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Muammo xabarini faqat ijarachi yuboradi")
    report = MaintenanceReport(
        rental_id=rental.id,
        listing_id=rental.listing_id,
        reporter_id=current_user.id,
        recipient_id=listing.owner_id,
        text=payload.text,
        image_url=payload.image_url,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.post("/{rental_id}/repost-vacancy")
async def repost_vacancy(
    rental_id: uuid.UUID,
    payload: VacancyRepostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    rental = await db.get(Rental, rental_id)
    if rental is None or not rental.is_active:
        raise HTTPException(status_code=404, detail="Faol rental topilmadi")
    if rental.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Faqat shu xonada yashayotgan user reklama bera oladi")
    source_listing = await db.get(Listing, rental.listing_id)
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
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return {"success": True, "listing_id": str(listing.id), "message": "Birinchi vacancy reklamasi bepul joylandi"}


@router.patch("/{rental_id}/close", response_model=RentalOut)
async def close_rental(
    rental_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rental:
    result = await db.execute(select(Rental).where(Rental.id == rental_id))
    rental = result.scalar_one_or_none()
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental topilmadi")
    listing = await db.get(Listing, rental.listing_id)
    is_owner = listing is not None and listing.owner_id == current_user.id
    is_tenant = rental.student_id == current_user.id
    is_admin = current_user.role == UserRole.admin
    if not (is_owner or is_tenant or is_admin):
        raise HTTPException(status_code=403, detail="Bu ijarani yopishga ruxsat yo'q")
    rental.is_active = False
    if listing is not None:
        listing.available_spaces = min(listing.max_guests, listing.available_spaces + 1)
        listing.is_active = True
    await db.commit()
    await db.refresh(rental)
    return rental
