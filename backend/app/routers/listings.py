from __future__ import annotations

import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user, require_role
from app.models.listing import Listing, ListingSource
from app.models.listing_payment import ListingPayment, ListingPaymentStatus, ListingPaymentType
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
from database.operations.delete import listings as delete_listings
from database.operations.insert import listings as insert_listings
from database.operations.select import listings as select_listings
from database.operations.select import subscriptions as select_subscriptions
from database.operations.update import listings as update_listings
from database.operations.update import subscriptions as update_subscriptions

router = APIRouter()


def _parse_listing_id(listing_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(listing_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Listing not found") from exc


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


def _row_to_card(row, now: datetime) -> ListingCard:
    listing, owner_role, owner_name, owner_phone, owner_verified, rating, review_count = row
    return ListingCard(
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

    simple_count = await select_listings.count_active_simple(db, current_user.id)
    premium_count = await select_listings.count_active_premium(db, current_user.id, now)

    if wants_premium:
        if premium_count >= limits.premium_limit:
            raise HTTPException(status_code=403, detail="Premium listing limiti tugagan")
    elif simple_count >= limits.simple_limit:
        raise HTTPException(status_code=403, detail="Simple listing limiti tugagan")


async def _maybe_consume_subscription(db: AsyncSession, user: User, is_premium: bool) -> bool:
    if (not user.role or user.role != UserRole.makler) or is_premium:
        return False

    today = datetime.now(timezone.utc).date()
    sub = await select_subscriptions.get_active_subscription(db, user.id, today)
    if sub is None:
        return False

    await update_subscriptions.increment_used_count(db, sub.id)
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
    await insert_listings.create_listing(db, listing)

    used_subscription = await _maybe_consume_subscription(db, current_user, payload.is_premium)
    payment_amount = 0 if used_subscription else _get_listing_fee(current_user.role, payload.is_premium)
    await insert_listings.create_listing_payment(
        db,
        ListingPayment(
            listing_id=listing.id,
            user_id=current_user.id,
            amount=payment_amount,
            type=ListingPaymentType.premium if payload.is_premium else ListingPaymentType.regular,
            status=ListingPaymentStatus.paid if payment_amount == 0 else ListingPaymentStatus.pending,
        ),
    )
    return await insert_listings.commit_listing(db, listing)


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
    washer: Optional[bool] = None,
    fridge: Optional[bool] = None,
    kitchenware: Optional[bool] = None,
    move_in_ready: bool = False,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ListingSearchResponse:
    from app.models.listing import Listing
    from app.models.user import User

    now = datetime.now(timezone.utc)
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
    if washer is not None:
        filters.append(Listing.amenities["washer"].as_boolean() == washer)
    if fridge is not None:
        filters.append(Listing.amenities["fridge"].as_boolean() == fridge)
    if kitchenware is not None:
        filters.append(Listing.amenities["kitchenware"].as_boolean() == kitchenware)

    if move_in_ready:
        filters.extend(
            [
                Listing.amenities["wifi"].as_boolean().is_(True),
                Listing.amenities["gas"].as_boolean().is_(True),
                Listing.amenities["water"].as_boolean().is_(True),
                Listing.amenities["fridge"].as_boolean().is_(True),
                Listing.amenities["kitchenware"].as_boolean().is_(True),
                Listing.amenities["washer"].as_boolean().is_(True),
            ]
        )

    try:
        result_rows, total, pages = await select_listings.search_with_cards(
            db, filters=filters, page=page, limit=limit, now=now
        )
    except (TimeoutError, OSError, SQLAlchemyError):
        return ListingSearchResponse(
            success=False,
            message="Database temporarily unavailable",
            listings=[],
            total=0,
            page=page,
            pages=1,
        )

    cards = [_row_to_card(row, now) for row in result_rows]
    return ListingSearchResponse(listings=cards, total=total, page=page, pages=pages)


@router.get("/me", response_model=list[ListingCard])
async def get_my_listings(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ListingCard]:
    now = datetime.now(timezone.utc)
    rows = await select_listings.get_my_listing_rows(db, current_user.id, page=page, limit=limit)
    return [_row_to_card(row, now) for row in rows]


@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> dict:
    row = await select_listings.get_with_owner(db, _parse_listing_id(listing_id))
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
        "owner_role": owner.role.value if owner.role else "owner",
        "owner_verified": owner.is_verified,
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
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
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

    if payload.is_premium is True and listing.premium_expires_at is None:
        updates["premium_expires_at"] = datetime.now(timezone.utc) + timedelta(days=30)

    return await update_listings.apply_fields(db, listing, **updates)


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
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi o'chira oladi")

    if await select_listings.has_rental_history(db, listing.id):
        raise HTTPException(status_code=409, detail="Bu e'londa ijara tarixi bor. Avval uni nofaol qiling yoki admin orqali arxivlang.")

    await delete_listings.delete_listing(db, listing)
    return ActivateListingResponse(message="Listing o'chirildi")


@router.post("/{listing_id}/activate-basic", response_model=ActivateListingResponse)
async def activate_basic_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi reklamaga chiqara oladi")

    await update_listings.activate_basic(db, listing.id)
    await insert_listings.create_listing_payment(
        db,
        ListingPayment(
            listing_id=listing.id,
            user_id=current_user.id,
            amount=_get_listing_fee(current_user.role, False),
            type=ListingPaymentType.regular,
            status=ListingPaymentStatus.pending,
        ),
    )
    await db.commit()
    return ActivateListingResponse()


@router.post("/{listing_id}/upgrade-to-premium", response_model=UpgradeToPremiumResponse)
async def upgrade_to_premium(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UpgradeToPremiumResponse:
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi premiumga ko'tara oladi")

    premium_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    await update_listings.upgrade_to_premium(db, listing.id, premium_expires_at)
    await insert_listings.create_listing_payment(
        db,
        ListingPayment(
            listing_id=listing.id,
            user_id=current_user.id,
            amount=_get_listing_fee(current_user.role, True),
            type=ListingPaymentType.premium,
            status=ListingPaymentStatus.pending,
        ),
    )
    await db.commit()
    return UpgradeToPremiumResponse(premium_expires_at=premium_expires_at)


@router.post("/{listing_id}/mark-occupied", response_model=ActivateListingResponse)
async def mark_listing_occupied(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi holatni o'zgartira oladi")

    await update_listings.mark_occupied(db, listing)
    return ActivateListingResponse(message="Listing band qilindi")


@router.post("/{listing_id}/mark-available", response_model=ActivateListingResponse)
async def mark_listing_available(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Faqat listing egasi holatni o'zgartira oladi")

    await update_listings.mark_available(db, listing)
    return ActivateListingResponse(message="Listing yana bo'sh qilindi")
