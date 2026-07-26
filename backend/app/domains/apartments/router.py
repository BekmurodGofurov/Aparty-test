"""Apartments domain — FastAPI router.

Merges:
  - /apartments/*  (popular, search, detail, view tracking, cache management)
  - /listings/*    (CRUD, premium upgrade, activate, mark-occupied)
  - /locations/*   (static metadata)
  - /favorites/*   (toggle, list)
  - /ai/*          (AI chat for listing assistance)

URL prefixes are assigned in main.py via include_router().
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

from app.core.cache import (
    DETAIL_PAGE_JITTER,
    DETAIL_PAGE_TTL,
    HEAVY_SEARCH_JITTER,
    HEAVY_SEARCH_TTL,
    POPULAR_APARTMENTS_KEY,
    STATIC_DATA_JITTER,
    STATIC_DATA_TTL,
    CacheManager,
    cached,
    etag,
)
from app.core.database import get_db
from app.domains.apartments.models import Favorite, Listing, ListingSource, ListingTargetGender
from app.domains.apartments.schemas import (
    ActivateListingResponse,
    ListingCard,
    ListingCreate,
    ListingOut,
    ListingSearchResponse,
    ListingUpdate,
    PopularApartmentItem,
    PopularApartmentsResponse,
    UpgradeToPremiumResponse,
)
from app.domains.apartments.services import (
    ApartmentService,
    ListingLimit,
    TRIAL_MONTHS,
    get_listing_limit_for_role,
)
from app.domains.apartments.view_sync import increment_apartment_view
from app.domains.users.models import User, UserRole
from app.domains.users.services import (
    get_current_user,
    get_optional_current_user,
    require_role,
)
from database.operations.delete import favorites as delete_favorites
from database.operations.delete import listings as delete_listings
from database.operations.insert import favorites as insert_favorites
from database.operations.insert import listings as insert_listings
from database.operations.select import favorites as select_favorites
from database.operations.select import listings as select_listings
from database.operations.select import subscriptions as select_subscriptions
from database.operations.update import listings as update_listings
from database.operations.update import subscriptions as update_subscriptions
from app.domains.orders.models import ListingPayment, ListingPaymentStatus, ListingPaymentType

from app.domains.apartments.ai_service import ai_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ===========================================================================
# Helpers
# ===========================================================================


def _parse_listing_id(listing_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(listing_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Listing not found") from exc


def _is_premium_active(
    is_premium: bool, premium_expires_at: Optional[datetime], now: datetime
) -> bool:
    return ApartmentService.is_premium_active(is_premium, premium_expires_at, now)


def _get_listing_fee(role: UserRole, is_premium: bool) -> int:
    if is_premium:
        return 40 if role == UserRole.owner else 30
    return 5 if role == UserRole.owner else 3


def _source_for_role(role: UserRole) -> Optional[ListingSource]:
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
    db: AsyncSession, current_user: User, wants_premium: bool
) -> None:
    role_name = current_user.role.value if current_user.role else "student"
    limits = get_listing_limit_for_role(role_name)
    if limits.simple_limit == 0 and limits.premium_limit == 0:
        raise HTTPException(403, "Siz listing yarata olmaysiz")

    now = datetime.now(timezone.utc)
    created_at = current_user.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    trial_ends_at = created_at + timedelta(days=TRIAL_MONTHS * 30)
    if now > trial_ends_at:
        raise HTTPException(403, "Bepul trial muddati tugagan")

    simple_count = await select_listings.count_active_simple(db, current_user.id)
    premium_count = await select_listings.count_active_premium(db, current_user.id, now)

    if wants_premium:
        if premium_count >= limits.premium_limit:
            raise HTTPException(403, "Premium listing limiti tugagan")
    elif simple_count >= limits.simple_limit:
        raise HTTPException(403, "Simple listing limiti tugagan")


async def _maybe_consume_subscription(
    db: AsyncSession, user: User, is_premium: bool
) -> bool:
    if (not user.role or user.role != UserRole.makler) or is_premium:
        return False
    today = datetime.now(timezone.utc).date()
    sub = await update_subscriptions.try_consume_with_lock(db, user.id, today)
    if sub is None:
        has_sub = await select_subscriptions.get_active_by_user(db, user.id)
        if has_sub:
            raise HTTPException(403, "Subscription limit reached")
        return False
    return True


# ===========================================================================
# Apartments: popular / search / detail / view-tracking
# ===========================================================================


@router.get("/popular", response_model=PopularApartmentsResponse, tags=["Apartments"])
async def get_popular_apartments(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return the top-20 most-viewed active listings (cache-aside)."""
    redis = request.app.state.redis
    cache_mgr = CacheManager(redis)

    cached_data = await cache_mgr.get(POPULAR_APARTMENTS_KEY)
    if cached_data is not None:
        response = PopularApartmentsResponse(
            apartments=cached_data, total=len(cached_data), cached=True
        )
        return JSONResponse(content=response.model_dump(mode="json"), headers={"X-Cache": "HIT"})

    stmt = (
        select(Listing)
        .where(Listing.is_active == True)  # noqa: E712
        .order_by(Listing.views_count.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    listings = result.scalars().all()

    apartments = [PopularApartmentItem.model_validate(listing) for listing in listings]
    apartments_json = [apt.model_dump(mode="json") for apt in apartments]

    await cache_mgr.set(
        POPULAR_APARTMENTS_KEY, apartments_json, ttl=HEAVY_SEARCH_TTL, jitter_range=HEAVY_SEARCH_JITTER
    )
    response = PopularApartmentsResponse(
        apartments=apartments_json, total=len(apartments_json), cached=False
    )
    return JSONResponse(content=response.model_dump(mode="json"), headers={"X-Cache": "MISS"})


@router.get("/search", tags=["Apartments"])
@cached(key_template="aparty:apartments:search", ttl=HEAVY_SEARCH_TTL, jitter_range=HEAVY_SEARCH_JITTER)
async def search_apartments(
    request: Request,
    region: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    rooms_count: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Heavy search with filters — cached 5 mins with jitter."""
    stmt = select(Listing).where(Listing.is_active == True)  # noqa: E712
    if region:
        stmt = stmt.where(Listing.region == region)
    if district:
        stmt = stmt.where(Listing.district == district)
    if min_price is not None:
        stmt = stmt.where(Listing.price_usd >= min_price)
    if max_price is not None:
        stmt = stmt.where(Listing.price_usd <= max_price)
    if rooms_count is not None:
        stmt = stmt.where(Listing.rooms_count == rooms_count)

    result = await db.execute(stmt)
    listings = result.scalars().all()
    items = [PopularApartmentItem.model_validate(l).model_dump(mode="json") for l in listings]
    return {"results": items, "total": len(items)}


@router.get("/{apartment_id}", tags=["Apartments"])
@cached(
    key_template="aparty:apartments:detail:{apartment_id}",
    ttl=DETAIL_PAGE_TTL,
    jitter_range=DETAIL_PAGE_JITTER,
)
async def get_apartment_detail(
    apartment_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Single apartment detail page — cached 30 mins with jitter."""
    stmt = select(Listing).where(Listing.id == apartment_id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Apartment not found")
    return PopularApartmentItem.model_validate(listing).model_dump(mode="json")


@router.delete("/popular/cache", tags=["Apartments"])
async def invalidate_popular_cache(request: Request) -> dict[str, str]:
    """Manually invalidate the popular apartments cache."""
    redis = request.app.state.redis
    cache_mgr = CacheManager(redis)
    await cache_mgr.delete(POPULAR_APARTMENTS_KEY)
    return {"status": "invalidated"}


@router.post("/{apartment_id}/view", status_code=status.HTTP_202_ACCEPTED, tags=["Apartments"])
async def track_apartment_view(
    apartment_id: uuid.UUID, request: Request
) -> dict:
    """Increment apartment view count asynchronously via Redis."""
    await increment_apartment_view(apartment_id, request.app.state.redis)
    return {"message": "View recorded", "apartment_id": str(apartment_id)}


# ===========================================================================
# Listings: CRUD
# ===========================================================================


@router.post("", response_model=ListingOut, status_code=status.HTTP_201_CREATED, include_in_schema=False, tags=["Listings"])
@router.post("/listings/", response_model=ListingOut, status_code=status.HTTP_201_CREATED, tags=["Listings"])
async def create_listing(
    payload: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("makler", "owner")),
) -> Listing:
    """Create a new listing."""
    source = _source_for_role(current_user.role)
    if source is None:
        raise HTTPException(403, "Siz listing yarata olmaysiz")

    await _enforce_listing_limits(db=db, current_user=current_user, wants_premium=payload.is_premium)

    premium_expires_at = (
        datetime.now(timezone.utc) + timedelta(days=30) if payload.is_premium else None
    )
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


@router.get("/listings/search", response_model=ListingSearchResponse, tags=["Listings"])
@cache(expire=300)
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
    """Comprehensive listing search with all filters."""
    from app.domains.users.models import User as UserModel

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
        filters.append(UserModel.role == owner_role)
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
        filters.extend([
            Listing.amenities["wifi"].as_boolean().is_(True),
            Listing.amenities["gas"].as_boolean().is_(True),
            Listing.amenities["water"].as_boolean().is_(True),
            Listing.amenities["fridge"].as_boolean().is_(True),
            Listing.amenities["kitchenware"].as_boolean().is_(True),
            Listing.amenities["washer"].as_boolean().is_(True),
        ])

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


@router.get("/listings/me", response_model=list[ListingCard], tags=["Listings"])
async def get_my_listings(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ListingCard]:
    """Get all listings belonging to the current user."""
    now = datetime.now(timezone.utc)
    rows = await select_listings.get_my_listing_rows(db, current_user.id, page=page, limit=limit)
    return [_row_to_card(row, now) for row in rows]


@router.get("/listings/{listing_id}", response_model=ListingOut, tags=["Listings"])
async def get_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> dict:
    """Get full listing details by ID."""
    row = await select_listings.get_with_owner(db, _parse_listing_id(listing_id))
    if row is None:
        raise HTTPException(404, "Listing topilmadi")
    listing, owner = row
    if not listing.is_active:
        is_owner = current_user is not None and listing.owner_id == current_user.id
        is_admin = current_user is not None and current_user.role == UserRole.admin
        if not (is_owner or is_admin):
            raise HTTPException(404, "Listing topilmadi")
    return {
        "id": listing.id, "owner_id": listing.owner_id,
        "owner_full_name": owner.full_name, "owner_phone": owner.phone,
        "owner_role": owner.role.value if owner.role else "owner",
        "owner_verified": owner.is_verified,
        "region": listing.region, "district": listing.district,
        "address": listing.address, "building_number": listing.building_number,
        "room_number": listing.room_number, "floor": listing.floor,
        "total_floors": listing.total_floors, "latitude": listing.latitude,
        "longitude": listing.longitude, "rooms_count": listing.rooms_count,
        "area_m2": listing.area_m2, "price_usd": listing.price_usd,
        "target_gender": listing.target_gender, "source": listing.source,
        "max_guests": listing.max_guests, "available_spaces": listing.available_spaces,
        "amenities": listing.amenities or {}, "images": listing.images or [],
        "description": listing.description, "is_premium": listing.is_premium,
        "premium_expires_at": listing.premium_expires_at, "is_active": listing.is_active,
        "views_count": listing.views_count, "created_at": listing.created_at,
    }


@router.patch("/listings/{listing_id}", response_model=ListingOut, tags=["Listings"])
@router.put("/listings/{listing_id}", response_model=ListingOut, tags=["Listings"])
async def update_listing(
    listing_id: str,
    payload: ListingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Listing:
    """Update listing fields (partial or full)."""
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(404, "Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Faqat listing egasi tahrirlay oladi")

    updates = payload.model_dump(exclude_unset=True)
    wants_premium = bool(updates.get("is_premium", listing.is_premium))
    is_admin = current_user.role == UserRole.admin

    if "is_active" in updates and not is_admin:
        raise HTTPException(403, "Listingni reklama orqali aktiv qilish kerak")
    if wants_premium and not listing.is_premium:
        await _enforce_listing_limits(db=db, current_user=current_user, wants_premium=True)
    if payload.is_premium is True and listing.premium_expires_at is None:
        updates["premium_expires_at"] = datetime.now(timezone.utc) + timedelta(days=30)

    return await update_listings.apply_fields(db, listing, **updates)


@router.delete("/listings/{listing_id}", response_model=ActivateListingResponse, tags=["Listings"])
async def delete_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    """Delete a listing."""
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(404, "Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Faqat listing egasi o'chira oladi")
    if await select_listings.has_rental_history(db, listing.id):
        raise HTTPException(409, "Bu e'londa ijara tarixi bor.")
    await delete_listings.delete_listing(db, listing)
    return ActivateListingResponse(message="Listing o'chirildi")


@router.post("/listings/{listing_id}/activate-basic", response_model=ActivateListingResponse, tags=["Listings"])
async def activate_basic_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(404, "Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Faqat listing egasi reklamaga chiqara oladi")
    await update_listings.activate_basic(db, listing.id)
    await insert_listings.create_listing_payment(
        db,
        ListingPayment(
            listing_id=listing.id, user_id=current_user.id,
            amount=_get_listing_fee(current_user.role, False),
            type=ListingPaymentType.regular, status=ListingPaymentStatus.pending,
        ),
    )
    await db.commit()
    return ActivateListingResponse()


@router.post("/listings/{listing_id}/upgrade-to-premium", response_model=UpgradeToPremiumResponse, tags=["Listings"])
async def upgrade_to_premium(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UpgradeToPremiumResponse:
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(404, "Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Faqat listing egasi premiumga ko'tara oladi")
    premium_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    await update_listings.upgrade_to_premium(db, listing.id, premium_expires_at)
    await insert_listings.create_listing_payment(
        db,
        ListingPayment(
            listing_id=listing.id, user_id=current_user.id,
            amount=_get_listing_fee(current_user.role, True),
            type=ListingPaymentType.premium, status=ListingPaymentStatus.pending,
        ),
    )
    await db.commit()
    return UpgradeToPremiumResponse(premium_expires_at=premium_expires_at)


@router.post("/listings/{listing_id}/mark-occupied", response_model=ActivateListingResponse, tags=["Listings"])
async def mark_listing_occupied(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(404, "Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Faqat listing egasi holatni o'zgartira oladi")
    await update_listings.mark_occupied(db, listing)
    return ActivateListingResponse(message="Listing band qilindi")


@router.post("/listings/{listing_id}/mark-available", response_model=ActivateListingResponse, tags=["Listings"])
async def mark_listing_available(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivateListingResponse:
    listing = await select_listings.get_by_id(db, _parse_listing_id(listing_id))
    if listing is None:
        raise HTTPException(404, "Listing topilmadi")
    if listing.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Faqat listing egasi holatni o'zgartira oladi")
    await update_listings.mark_available(db, listing)
    return ActivateListingResponse(message="Listing yana bo'sh qilindi")


# ===========================================================================
# Locations (static metadata)
# ===========================================================================


@router.get("/locations", tags=["Locations"])
@router.get("/locations/", tags=["Locations"])
@etag
@cached(key_template="aparty:locations:all", ttl=STATIC_DATA_TTL, jitter_range=STATIC_DATA_JITTER)
async def get_locations(request: Request) -> dict:
    """Static metadata — cached 24h + ETag support."""
    return {
        "regions": [
            "Toshkent shahri", "Andijon viloyati", "Farg'ona viloyati",
            "Namangan viloyati", "Samarqand viloyati", "Buxoro viloyati",
        ],
        "metro_stations": [
            "Amir Temur Xiyoboni", "Chorsu", "Yunusobod",
            "Buyuk Ipak Yo'li", "Paxtakor",
        ],
        "amenities": [
            {"id": "wifi", "name": "Wi-Fi"}, {"id": "ac", "name": "Konditsioner"},
            {"id": "washer", "name": "Kir yuvish mashinasi"}, {"id": "tv", "name": "Televizor"},
            {"id": "fridge", "name": "Muzlatgich"},
        ],
    }


# ===========================================================================
# Favorites
# ===========================================================================


@router.post("/favorites/{listing_id}", status_code=status.HTTP_201_CREATED, tags=["Favorites"])
async def toggle_favorite(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle favorite status for a listing."""
    existing = await select_favorites.get_by_user_and_listing(db, current_user.id, listing_id)
    if existing:
        await delete_favorites.delete(db, existing)
        return {"status": "removed"}
    listing = await select_listings.get_by_id(db, listing_id)
    if not listing:
        raise HTTPException(404, "Listing topilmadi")
    await insert_favorites.create(db, Favorite(user_id=current_user.id, listing_id=listing_id))
    return {"status": "added"}


@router.get("/favorites/me", response_model=list[ListingCard], tags=["Favorites"])
async def get_my_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all favorites for the current user."""
    now = datetime.now(timezone.utc)
    rows = await select_favorites.get_my_favorites_rows(db, current_user.id)
    cards: list[ListingCard] = []
    for listing, owner_role, owner_name, owner_verified, rating, review_count in rows:
        cards.append(
            ListingCard(
                id=listing.id, region=listing.region, district=listing.district,
                address=listing.address, latitude=listing.latitude, longitude=listing.longitude,
                rooms_count=listing.rooms_count, area_m2=listing.area_m2, floor=listing.floor,
                price_usd=listing.price_usd, target_gender=listing.target_gender,
                available_spaces=listing.available_spaces, amenities=listing.amenities or {},
                images=listing.images[:1] if listing.images else [],
                description=listing.description,
                is_premium=_is_premium_active(listing.is_premium, listing.premium_expires_at, now),
                is_active=listing.is_active, views_count=listing.views_count,
                premium_expires_at=listing.premium_expires_at,
                owner_role=owner_role.value if owner_role else "student",
                owner_full_name=owner_name or "", owner_verified=bool(owner_verified),
                rating=round(float(rating), 1) if rating is not None else None,
                reviews_count=int(review_count or 0), created_at=listing.created_at,
            )
        )
    return cards


# ===========================================================================
# AI Assistant
# ===========================================================================


class MessagePart(BaseModel):
    text: str


class ContentPart(BaseModel):
    role: str
    parts: list[MessagePart]


class ChatInput(BaseModel):
    message: str
    history: Optional[list[ContentPart]] = None


@router.post("/ai/chat", tags=["AI"])
async def chat_endpoint(
    payload: ChatInput,
    db: AsyncSession = Depends(get_db),
):
    """AI Chatbot for listing assistance."""
    try:
        history = []
        if payload.history:
            for h in payload.history:
                history.append({"role": h.role, "parts": [p.text for p in h.parts]})
        ai_result = await ai_service.chat(payload.message, db, history)
        return {"success": True, "response": ai_result["text"], "listings": ai_result.get("listings", [])}
    except Exception as e:
        raise HTTPException(500, str(e))
