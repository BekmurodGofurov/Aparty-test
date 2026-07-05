from __future__ import annotations

import math
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, delete, desc, func, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user, require_role
from app.models.listing import Listing, ListingSource, ListingTargetGender
from app.models.listing_payment import ListingPayment, ListingPaymentStatus, ListingPaymentType
from app.models.favorite import Favorite
from app.models.rental import Rental, RentalRequest, RentalRequestMessage
from app.models.review import Review
from app.models.subscription import Subscription
from app.models.user import User, UserRole
from app.services.listing_limits import TRIAL_MONTHS, get_listing_limit_for_role
from app.schemas.listing import (
    ListingCard,
    ListingCreate,
    ListingOut,
    ListingSearchResponse,
    ListingUpdate,
    ActivateListingResponse,
    UpgradeToPremiumResponse,
)

router = APIRouter()

ESSENTIAL_AMENITIES = {
    "wifi",
    "gas",
    "water",
    "tv",
    "ac",
    "washing_machine",
    "refrigerator",
    "kitchen_appliances",
}


def _is_premium_active(is_premium: bool, premium_expires_at: Optional[datetime], now: datetime) -> bool:
    if not is_premium or premium_expires_at is None:
        return False
    if premium_expires_at.tzinfo is None:
        premium_expires_at = premium_expires_at.replace(tzinfo=timezone.utc)
    return premium_expires_at > now


def _get_listing_fee(role: UserRole, is_premium: bool) -> int:
    if is_premium:
        return 40 if role == UserRole.owner else 30
    return 5 if role == UserRole.owner else 3


def _source_for_role(role: UserRole):
    if role == UserRole.makler:
        return ListingSource.makler
    if role == UserRole.owner:
        return ListingSource.owner
    return None


async def _enforce_listing_limits(
    db: AsyncSession,
    current_user: User,
    wants_premium: bool,
) -> None:
    role_name = current_user.role.value if current_user.role else "student"
    limits = get_listing_limit_for_role(role_name)
    if limits.simple_limit == 0 and limits.premium_limit == 0:
        raise HTTPException(status_code=403, detail="Siz listing yarata olmaysiz")

    now = datetime.now(timezone.utc)
    created_at = current_user.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    trial_ends_at = created_at + timedelta(days=TRIAL_MONTHS * 30)
    if now > trial_ends_at:
        raise HTTPException(status_code=403, detail="Bepul trial muddati tugagan")

    simple_count = await db.scalar(
        select(func.count(Listing.id)).where(
            Listing.owner_id == current_user.id,
            Listing.is_active.is_(True),
            Listing.is_premium.is_(False),
        )
    )
    premium_count = await db.scalar(
        select(func.count(Listing.id)).where(
            Listing.owner_id == current_user.id,
            Listing.is_active.is_(True),
            Listing.is_premium.is_(True),
            Listing.premium_expires_at.is_not(None),
            Listing.premium_expires_at > now,
        )
    )

    if wants_premium:
        if (premium_count or 0) >= limits.premium_limit:
            raise HTTPException(status_code=403, detail="Premium listing limiti tugagan")
    elif (simple_count or 0) >= limits.simple_limit:
        raise HTTPException(status_code=403, detail="Simple listing limiti tugagan")


async def _maybe_consume_subscription(db: AsyncSession, user: User, is_premium: bool) -> bool:
    if (not user.role or user.role != UserRole.makler) or is_premium:
        return False

    today = datetime.now(timezone.utc).date()
    sub = await db.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.is_active.is_(True),
            Subscription.start_date <= today,
            Subscription.end_date >= today,
            Subscription.used_count < Subscription.listing_limit,
        )
        .order_by(Subscription.created_at.desc())
    )
    if sub is None:
        return False

    sub.used_count += 1
    return True


@router.post("", response_model=ListingOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=ListingOut, status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("makler", "owner")),
) -> Listing:
    source = _source_for_role(current_user.role)
    if source is None:
        raise HTTPException(status_code=403, detail="Siz listing yarata olmaysiz")

    await _enforce_listing_limits(db=db, current_user=current_user, wants_premium=payload.is_premium)

    premium_expires_at = datetime.now(timezone.utc) + timedelta(days=30) if payload.is_premium else None
    listing_data = payload.model_dump()
    listing_data["source"] = source
    if current_user.role == UserRole.owner:
        listing_data["is_active"] = False
    listing = Listing(**listing_data, owner_id=current_user.id, premium_expires_at=premium_expires_at)
    db.add(listing)
    await db.flush()

    used_subscription = await _maybe_consume_subscription(db, current_user, payload.is_premium)
    payment_amount = 0 if used_subscription else _get_listing_fee(current_user.role, payload.is_premium)
    payment = ListingPayment(
        listing_id=listing.id,
        user_id=current_user.id,
        amount=payment_amount,
        type=ListingPaymentType.premium if payload.is_premium else ListingPaymentType.regular,
        status=ListingPaymentStatus.paid if payment_amount == 0 else ListingPaymentStatus.pending,
    )
    db.add(payment)

    await db.commit()
    await db.refresh(listing)
    return listing


@router.get("/search", response_model=ListingSearchResponse)
async def search_listings(
    region: Optional[str] = None,
    district: Optional[str] = None,
    price_min: Optional[int] = Query(default=None, ge=0),
    price_max: Optional[int] = Query(default=None, ge=0),
    target_gender: Optional[str] = None,
    rooms_count: Optional[int] = Query(default=None, ge=1),
    available_spaces: Optional[int] = Query(default=None, ge=1),
    apartment_type: Optional[str] = None,
    owner_role: Optional[str] = None,
    wifi: Optional[bool] = None,
    gas: Optional[bool] = None,
    water: Optional[bool] = None,
    tv: Optional[bool] = None,
    ac: Optional[bool] = None,
    washing_machine: Optional[bool] = None,
    refrigerator: Optional[bool] = None,
    kitchen_appliances: Optional[bool] = None,
    move_in_ready: bool = False,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ListingSearchResponse:
    now = datetime.now(timezone.utc)
    review_stats = (
        select(
            Review.listing_id.label("listing_id"),
            func.avg(Review.rating).label("rating"),
            func.count(Review.id).label("reviews_count"),
        )
        .group_by(Review.listing_id)
        .subquery()
    )

    filters = [Listing.is_active.is_(True)]

    if region:
        filters.append(Listing.region == region)
    if district:
        filters.append(Listing.district == district)
    if price_min is not None:
        filters.append(Listing.price_usd >= price_min)
    if price_max is not None:
        filters.append(Listing.price_usd <= price_max)
    if target_gender:
        filters.append(Listing.target_gender == target_gender)
    if apartment_type:
        if apartment_type == "dormitory":
            filters.append(Listing.rooms_count == 1)
        elif apartment_type == "apartment":
            filters.append(Listing.rooms_count >= 2)
    if rooms_count:
        filters.append(Listing.rooms_count >= rooms_count)
    if available_spaces:
        filters.append(Listing.available_spaces >= available_spaces)
    if owner_role:
        filters.append(User.role == owner_role)
    if wifi is not None:
        filters.append(Listing.amenities["wifi"].as_boolean() == wifi)
    if gas is not None:
        filters.append(Listing.amenities["gas"].as_boolean() == gas)
    if water is not None:
        filters.append(Listing.amenities["water"].as_boolean() == water)
    if tv is not None:
        filters.append(Listing.amenities["tv"].as_boolean() == tv)
    if ac is not None:
        filters.append(Listing.amenities["ac"].as_boolean() == ac)
    if washing_machine is not None:
        filters.append(Listing.amenities["washing_machine"].as_boolean() == washing_machine)
    if refrigerator is not None:
        filters.append(Listing.amenities["refrigerator"].as_boolean() == refrigerator)
    if kitchen_appliances is not None:
        filters.append(Listing.amenities["kitchen_appliances"].as_boolean() == kitchen_appliances)

    if move_in_ready:
        filters.extend(
            [
                Listing.amenities["wifi"].as_boolean().is_(True),
                Listing.amenities["gas"].as_boolean().is_(True),
                Listing.amenities["water"].as_boolean().is_(True),
                Listing.amenities["refrigerator"].as_boolean().is_(True),
                Listing.amenities["kitchen_appliances"].as_boolean().is_(True),
                Listing.amenities["washing_machine"].as_boolean().is_(True),
            ]
        )

    premium_sort = case(
        (and_(Listing.is_premium.is_(True), Listing.premium_expires_at.is_not(None), Listing.premium_expires_at > now), 1),
        else_=0,
    )

    base_query = (
        select(
            Listing,
            User.role.label("owner_role"),
            User.full_name.label("owner_full_name"),
            User.phone.label("owner_phone"),
            User.is_verified.label("owner_verified"),
            review_stats.c.rating,
            func.coalesce(review_stats.c.reviews_count, 0).label("reviews_count"),
        )
        .join(User, Listing.owner_id == User.id)
        .outerjoin(review_stats, review_stats.c.listing_id == Listing.id)
        .where(and_(*filters))
    )
    try:
        total = await db.scalar(select(func.count()).select_from(base_query.subquery()))
        total = total or 0
        pages = max(1, math.ceil(total / limit)) if total else 1
        offset = (page - 1) * limit

        rows = await db.execute(
            base_query
            .order_by(desc(premium_sort), desc(Listing.created_at))
            .offset(offset)
            .limit(limit)
        )
        result_rows = rows.all()
    except (TimeoutError, OSError, SQLAlchemyError):
        return ListingSearchResponse(
            success=False,
            message="Database temporarily unavailable",
            listings=[],
            total=0,
            page=page,
            pages=1,
        )

    cards: list[ListingCard] = []
    for listing, owner_role, owner_name, owner_phone, owner_verified, rating, review_count in result_rows:
        cards.append(
            ListingCard(
                id=listing.id,
                region=listing.region,
                district=listing.district,
                address=listing.address,
                latitude=listing.latitude,
                longitude=listing.longitude,
                rooms_count=listing.rooms_count,
                area_m2=listing.area_m2,
                floor=listing.floor,
                price_usd=listing.price_usd,
                target_gender=listing.target_gender,
                available_spaces=listing.available_spaces,
                amenities=listing.amenities or {},
                images=listing.images[:1] if listing.images else [],
                description=listing.description,
                is_premium=_is_premium_active(listing.is_premium, listing.premium_expires_at, now),
                is_active=listing.is_active,
                views_count=listing.views_count,
                premium_expires_at=listing.premium_expires_at,
                owner_role=owner_role.value if owner_role else "student",
                owner_full_name=owner_name,
                owner_phone=owner_phone,
                owner_verified=bool(owner_verified),
                rating=round(float(rating), 1) if rating is not None else None,
                reviews_count=int(review_count or 0),
                created_at=listing.created_at,
            )
        )

    return ListingSearchResponse(listings=cards, total=total, page=page, pages=pages)


@router.get("/me", response_model=list[ListingCard])
async def get_my_listings(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ListingCard]:
    now = datetime.now(timezone.utc)
    review_stats = (
        select(
            Review.listing_id.label("listing_id"),
            func.avg(Review.rating).label("rating"),
            func.count(Review.id).label("reviews_count"),
        )
        .group_by(Review.listing_id)
        .subquery()
    )
    rows = await db.execute(
        select(
            Listing,
            User.role.label("owner_role"),
            User.full_name.label("owner_full_name"),
            User.phone.label("owner_phone"),
            User.is_verified.label("owner_verified"),
            review_stats.c.rating,
            func.coalesce(review_stats.c.reviews_count, 0).label("reviews_count"),
        )
        .join(User, Listing.owner_id == User.id)
        .outerjoin(review_stats, review_stats.c.listing_id == Listing.id)
        .where(Listing.owner_id == current_user.id)
        .order_by(desc(Listing.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )

    cards: list[ListingCard] = []
    for listing, owner_role, owner_name, owner_phone, owner_verified, rating, review_count in rows.all():
        cards.append(
            ListingCard(
                id=listing.id,
                region=listing.region,
                district=listing.district,
                address=listing.address,
                latitude=listing.latitude,
                longitude=listing.longitude,
                rooms_count=listing.rooms_count,
                area_m2=listing.area_m2,
                floor=listing.floor,
                price_usd=listing.price_usd,
                target_gender=listing.target_gender,
                available_spaces=listing.available_spaces,
                amenities=listing.amenities or {},
                images=listing.images[:1] if listing.images else [],
                description=listing.description,
                is_premium=_is_premium_active(listing.is_premium, listing.premium_expires_at, now),
                is_active=listing.is_active,
                views_count=listing.views_count,
                premium_expires_at=listing.premium_expires_at,
                owner_role=owner_role.value if owner_role else "student",
                owner_full_name=owner_name,
                owner_phone=owner_phone,
                owner_verified=bool(owner_verified),
                rating=round(float(rating), 1) if rating is not None else None,
                reviews_count=int(review_count or 0),
                created_at=listing.created_at,
            )
        )
    return cards


@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> dict:
    result = await db.execute(
        select(Listing, User)
        .join(User, Listing.owner_id == User.id)
        .where(Listing.id == listing_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    listing, owner = row
    if not listing.is_active:
        is_owner = current_user is not None and listing.owner_id == current_user.id
        is_admin = current_user is not None and current_user.role == UserRole.admin
        if not (is_owner or is_admin):
            raise HTTPException(status_code=404, detail="Listing topilmadi")
    return {
        "id": listing.id,
        "owner_id": listing.owner_id,
        "owner_full_name": owner.full_name,
        "owner_phone": owner.phone,
        "region": listing.region,
        "district": listing.district,
        "address": listing.address,
        "building_number": listing.building_number,
        "room_number": listing.room_number,
        "floor": listing.floor,
        "total_floors": listing.total_floors,
        "latitude": listing.latitude,
        "longitude": listing.longitude,
        "rooms_count": listing.rooms_count,
        "area_m2": listing.area_m2,
        "price_usd": listing.price_usd,
        "target_gender": listing.target_gender,
        "source": listing.source,
        "max_guests": listing.max_guests,
        "available_spaces": listing.available_spaces,
        "amenities": listing.amenities or {},
        "images": listing.images or [],
        "description": listing.description,
        "is_premium": listing.is_premium,
        "premium_expires_at": listing.premium_expires_at,
        "is_active": listing.is_active,
        "views_count": listing.views_count,
        "created_at": listing.created_at,
    }


@router.patch("/{listing_id}", response_model=ListingOut)
async def update_listing(
    listing_id: str,
    payload: ListingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Listing:
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")

    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi tahrirlay oladi")

    updates = payload.model_dump(exclude_unset=True)
    wants_premium = bool(updates.get("is_premium", listing.is_premium))
    is_admin = current_user.role == UserRole.admin

    if "is_active" in updates and not is_admin:
        raise HTTPException(status_code=403, detail="Listingni reklama orqali aktiv qilish kerak")

    if wants_premium and not listing.is_premium:
        await _enforce_listing_limits(db=db, current_user=current_user, wants_premium=True)

    for key, value in updates.items():
        setattr(listing, key, value)

    if payload.is_premium is True and listing.premium_expires_at is None:
        listing.premium_expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    await db.commit()
    await db.refresh(listing)
    return listing


@router.put("/{listing_id}", response_model=ListingOut)
async def replace_listing(
    listing_id: str,
    payload: ListingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Listing:
    return await update_listing(listing_id, payload, db, current_user)


@router.delete("/{listing_id}", response_model=ActivateListingResponse)
async def delete_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi o'chira oladi")

    has_rental = await db.scalar(select(Rental.id).where(Rental.listing_id == listing.id).limit(1))
    if has_rental:
        raise HTTPException(status_code=409, detail="Bu e'londa ijara tarixi bor. Avval uni nofaol qiling yoki admin orqali arxivlang.")

    request_ids = select(RentalRequest.id).where(RentalRequest.listing_id == listing.id)
    await db.execute(delete(RentalRequestMessage).where(RentalRequestMessage.request_id.in_(request_ids)))
    await db.execute(delete(RentalRequest).where(RentalRequest.listing_id == listing.id))
    await db.execute(delete(Favorite).where(Favorite.listing_id == listing.id))
    await db.execute(delete(Review).where(Review.listing_id == listing.id))
    await db.execute(delete(ListingPayment).where(ListingPayment.listing_id == listing.id))
    await db.delete(listing)
    await db.commit()
    return ActivateListingResponse(message="Listing o'chirildi")


@router.post("/{listing_id}/activate-basic", response_model=ActivateListingResponse)
async def activate_basic_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi reklamaga chiqara oladi")

    await db.execute(
        update(Listing)
        .where(Listing.id == listing.id)
        .values(is_active=True, is_premium=False, premium_expires_at=None)
    )
    db.add(
        ListingPayment(
            listing_id=listing.id,
            user_id=current_user.id,
            amount=_get_listing_fee(current_user.role, False),
            type=ListingPaymentType.regular,
            status=ListingPaymentStatus.pending,
        )
    )
    await db.commit()
    return ActivateListingResponse()


@router.post("/{listing_id}/upgrade-to-premium", response_model=UpgradeToPremiumResponse)
async def upgrade_to_premium(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UpgradeToPremiumResponse:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi premiumga ko'tara oladi")

    premium_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    await db.execute(
        update(Listing)
        .where(Listing.id == listing.id)
        .values(is_premium=True, is_active=True, premium_expires_at=premium_expires_at)
    )
    db.add(
        ListingPayment(
            listing_id=listing.id,
            user_id=current_user.id,
            amount=_get_listing_fee(current_user.role, True),
            type=ListingPaymentType.premium,
            status=ListingPaymentStatus.pending,
        )
    )
    await db.commit()
    return UpgradeToPremiumResponse(premium_expires_at=premium_expires_at)


@router.post("/{listing_id}/mark-occupied", response_model=ActivateListingResponse)
async def mark_listing_occupied(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi holatni o'zgartira oladi")

    listing.available_spaces = 0
    listing.is_active = False
    await db.commit()
    return ActivateListingResponse(message="Listing band qilindi")


@router.post("/{listing_id}/mark-available", response_model=ActivateListingResponse)
async def mark_listing_available(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi holatni o'zgartira oladi")

    listing.available_spaces = max(1, listing.max_guests)
    listing.is_active = True
    await db.commit()
    return ActivateListingResponse(message="Listing yana bo'sh qilindi")
