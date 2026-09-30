"""Catalog Service Listings Router (`/api/v1/listings`)."""

from __future__ import annotations

import math
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.clients.iam import PublicProfile, fetch_public_profiles
from app.config import settings
from app.constants import API_PREFIX, DEFAULT_LISTING_TITLE, DEFAULT_PAGE_SIZE, LISTING_CREATOR_ROLES, MAX_PAGE_SIZE, MAX_ROOMMATE_SPACES, ROOMMATE_CREATOR_ROLES
from app.database import get_db
from app.events import LISTING_CREATED, LISTING_UPDATED, publish_listing_event
from app.mappers import (
    STUDENT_SOURCES,
    listing_to_card,
    listing_to_out,
    property_type_from_rental_type,
    rental_type_from_property_type,
    source_for_role,
)
from app.models import Listing, ListingImage, ListingSource, ListingStatus, ListingTargetGender
from app.schemas import (
    ActivateListingResponse,
    ListingBookingInfo,
    ListingCard,
    ListingCreate,
    ListingOut,
    ListingSearchResponse,
    ListingUpdate,
    RentalType,
    RoommateListingCreate,
    UpgradeToPremiumResponse,
)
from app.security import CurrentUser, get_current_user_id, get_optional_user_id, require_roles
from app.services.favorites import favorite_listing_ids

router = APIRouter(prefix=f"{API_PREFIX}/listings", tags=["Listings"])

UPDATABLE_FIELDS = (
    "description",
    "status",
    "region",
    "district",
    "address",
    "building_number",
    "room_number",
    "floor",
    "total_floors",
    "latitude",
    "longitude",
    "rooms_count",
    "area_m2",
    "target_gender",
    "max_guests",
    "available_spaces",
    "amenities",
    "residents_male",
    "residents_female",
    "residents_children",
    "available_from",
    "is_premium",
    "premium_expires_at",
    "is_active",
)

UNPROCESSABLE_STATUS = 422
ROOMMATE_TITLE_PREFIX = "Roommate wanted: "

# Copied from the apartment onto its roommate listings.
APARTMENT_FIELDS_COPIED = (
    "region", "district", "address", "building_number", "room_number", "floor", "total_floors",
    "latitude", "longitude", "rooms_count", "area_m2",
)
# A roommate listing follows its apartment: these fields cannot be edited.
ROOMMATE_LOCKED_FIELDS = frozenset(
    {"region", "district", "address", "building_number", "room_number", "floor", "total_floors", "latitude",
     "longitude", "rooms_count", "area_m2", "max_guests", "rental_type"}
)

AMENITY_FILTERS = ("wifi", "gas", "water", "tv", "air_conditioner", "washing_machine", "fridge", "kitchen", "move_in_ready", "has_contract", "near_metro", "near_university")


def _image_record_data(item: Any, index: int) -> dict[str, Any]:
    """Normalize an image given as a URL string or an object into ListingImage fields."""
    if isinstance(item, str):
        item = {"image_url": item}
    if not isinstance(item, dict):
        item = {}

    image_url = item.get("image_url") or item.get("url") or item.get("display_url")
    if not image_url:
        raise HTTPException(
            status_code=UNPROCESSABLE_STATUS,
            detail="Each image must be a URL string or an object with image_url, url or display_url.",
        )

    return {
        "image_url": image_url,
        "delete_url": item.get("delete_url"),
        "is_primary": bool(item.get("is_primary", index == 0)),
    }


def _ad_expired(listing: Listing) -> bool:
    return listing.expires_at is not None and listing.expires_at <= datetime.now(timezone.utc)


def _fallback_title(payload: ListingCreate | ListingUpdate) -> Optional[str]:
    if payload.title:
        return payload.title
    parts = (payload.district, payload.region, payload.address)
    return ", ".join(part for part in parts if part) or None


def _apply_listing_payload(listing: Listing, payload: ListingCreate | ListingUpdate, *, is_create: bool) -> None:
    data = payload.model_dump(exclude_unset=not is_create, exclude={"images", "rental_type"})

    if is_create:
        listing.title = _fallback_title(payload) or DEFAULT_LISTING_TITLE
    elif payload.title:
        listing.title = payload.title

    if payload.price is not None:
        listing.price = float(payload.price)

    if payload.rental_type is not None:
        listing.property_type = property_type_from_rental_type(payload.rental_type)
    elif is_create:
        listing.property_type = RentalType.full_unit.value

    for field_name in UPDATABLE_FIELDS:
        if field_name in data:
            setattr(listing, field_name, data[field_name])

    if listing.status is None:
        listing.status = ListingStatus.active
    if listing.is_active is None:
        listing.is_active = listing.status != ListingStatus.deleted


async def _load_listing(id: uuid.UUID, db: AsyncSession) -> Listing:
    """Load a listing with images, or raise 404 if missing or soft-deleted."""
    result = await db.execute(select(Listing).options(selectinload(Listing.images)).where(Listing.id == id))
    listing = result.scalar_one_or_none()
    if not listing or listing.status == ListingStatus.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
    return listing


async def _get_owned_listing(id: uuid.UUID, owner_id: int, db: AsyncSession) -> Listing:
    listing = await _load_listing(id, db)
    if listing.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the listing owner can perform this action.",
        )
    return listing


async def _reload_listing(id: uuid.UUID, db: AsyncSession) -> Listing:
    """Reload a listing (including soft-deleted) after a commit."""
    result = await db.execute(select(Listing).options(selectinload(Listing.images)).where(Listing.id == id))
    return result.scalar_one()


async def owner_profiles(listings: list[Listing]) -> dict[int, PublicProfile]:
    return await fetch_public_profiles(listing.owner_id for listing in listings)


def _replace_images(listing: Listing, images: list[Any]) -> None:
    listing.images.clear()
    for index, image in enumerate(images):
        listing.images.append(ListingImage(listing_id=listing.id, **_image_record_data(image, index)))


async def _serialize(listing: Listing) -> dict[str, Any]:
    profiles = await owner_profiles([listing])
    return listing_to_out(listing, profiles.get(listing.owner_id))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ListingOut)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ListingOut, include_in_schema=False)
async def create_listing(
    payload: ListingCreate,
    user: CurrentUser = Depends(require_roles(*LISTING_CREATOR_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a listing (owners and maklers only)."""
    listing = Listing(
        owner_id=user.id, source=source_for_role(user.role), status=ListingStatus.active, is_active=True
    )
    _apply_listing_payload(listing, payload, is_create=True)

    db.add(listing)
    await db.flush()
    for index, image in enumerate(payload.images):
        db.add(ListingImage(listing_id=listing.id, **_image_record_data(image, index)))
    await db.commit()

    created = await _reload_listing(listing.id, db)
    await publish_listing_event(LISTING_CREATED, created)
    return await _serialize(created)


@router.post("/{apartment_id}/roommate", status_code=status.HTTP_201_CREATED, response_model=ListingOut)
async def create_roommate_listing(
    apartment_id: uuid.UUID,
    payload: RoommateListingCreate,
    user: CurrentUser = Depends(require_roles(*ROOMMATE_CREATOR_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """A tenant of this apartment looks for roommates. No permission is needed; the apartment's owner is notified."""
    apartment = await _load_listing(apartment_id, db)
    if apartment.parent_listing_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Post the ad for the apartment itself.")
    if apartment.owner_id == user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owners cannot post roommate ads for their own apartment.")

    # One active ad per apartment. Serialize per apartment so two quick requests cannot create two ads.
    await db.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"roommate:{apartment.id}"))))
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Listing)
        .where(
            Listing.parent_listing_id == apartment.id,
            Listing.status.in_([ListingStatus.active, ListingStatus.rented]),
            Listing.expires_at <= now,
        )
        .values(status=ListingStatus.archived, is_active=False)
    )
    existing_ad = await db.execute(
        select(Listing.id)
        .where(Listing.parent_listing_id == apartment.id, Listing.status.in_([ListingStatus.active, ListingStatus.rented]))
        .limit(1)
    )
    if existing_ad.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This apartment already has an active roommate ad.")

    listing = Listing(
        owner_id=user.id,
        source=ListingSource.roommate,
        status=ListingStatus.active,
        is_active=True,
        parent_listing_id=apartment.id,
        expires_at=now + timedelta(days=settings.roommate_listing_days),
        title=payload.title or f"{ROOMMATE_TITLE_PREFIX}{apartment.title}",
        description=payload.description,
        price=payload.price,
        property_type=RentalType.shared_room.value,
        target_gender=payload.target_gender,
        available_spaces=payload.available_spaces,
        max_guests=max(apartment.max_guests, payload.available_spaces),
        residents_male=payload.residents_male,
        residents_female=payload.residents_female,
        residents_children=payload.residents_children,
        available_from=payload.available_from,
        amenities=payload.amenities if payload.amenities is not None else dict(apartment.amenities or {}),
        **{field: getattr(apartment, field) for field in APARTMENT_FIELDS_COPIED},
    )
    db.add(listing)
    await db.flush()
    for image in sorted(apartment.images, key=lambda item: not item.is_primary):
        db.add(ListingImage(listing_id=listing.id, image_url=image.image_url, delete_url=None, is_primary=image.is_primary))
    await db.commit()

    created = await _reload_listing(listing.id, db)
    await publish_listing_event(
        LISTING_CREATED, created, apartment_owner_id=apartment.owner_id, apartment_title=apartment.title
    )
    return await _serialize(created)


@router.get("/search", response_model=ListingSearchResponse)
async def search_listings(
    region: Optional[str] = None,
    district: Optional[str] = None,
    target_gender: Optional[ListingTargetGender] = None,
    rental_type: Optional[RentalType] = None,
    owner_role: Optional[str] = None,
    price_min: Optional[int] = Query(None, ge=0),
    price_max: Optional[int] = Query(None, ge=0),
    rooms_count: Optional[int] = Query(None, ge=1),
    available_spaces: Optional[int] = Query(None, ge=0),
    wifi: Optional[bool] = None,
    gas: Optional[bool] = None,
    water: Optional[bool] = None,
    tv: Optional[bool] = None,
    air_conditioner: Optional[bool] = None,
    washing_machine: Optional[bool] = None,
    fridge: Optional[bool] = None,
    kitchen: Optional[bool] = None,
    move_in_ready: Optional[bool] = None,
    has_contract: Optional[bool] = None,
    near_metro: Optional[bool] = None,
    near_university: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user_id: Optional[int] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
) -> ListingSearchResponse:
    filters = [
        Listing.status == ListingStatus.active,
        Listing.is_active.is_(True),
        or_(Listing.expires_at.is_(None), Listing.expires_at > func.now()),
    ]

    if region:
        filters.append(Listing.region == region)
    if district:
        filters.append(Listing.district == district)
    if target_gender:
        filters.append(Listing.target_gender == target_gender)
    if rental_type:
        filters.append(Listing.property_type == rental_type.value)
    if owner_role == "makler":
        filters.append(Listing.source == ListingSource.makler)
    elif owner_role == "student":
        filters.append(Listing.source.in_(STUDENT_SOURCES))
    elif owner_role == "owner":
        filters.append(Listing.source != ListingSource.makler)
    if price_min is not None:
        filters.append(Listing.price >= price_min)
    if price_max is not None:
        filters.append(Listing.price <= price_max)
    if rooms_count is not None:
        filters.append(Listing.rooms_count >= rooms_count)
    if available_spaces is not None:
        filters.append(Listing.available_spaces >= available_spaces)

    amenity_values = {
        "wifi": wifi,
        "gas": gas,
        "water": water,
        "tv": tv,
        "air_conditioner": air_conditioner,
        "washing_machine": washing_machine,
        "fridge": fridge,
        "kitchen": kitchen,
        "move_in_ready": move_in_ready,
        "has_contract": has_contract,
        "near_metro": near_metro,
        "near_university": near_university,
    }
    for key in AMENITY_FILTERS:
        if amenity_values[key] is not None:
            filters.append(Listing.amenities[key].as_boolean() == amenity_values[key])

    total = (await db.execute(select(func.count()).select_from(Listing).where(*filters))).scalar_one()

    stmt = (
        select(Listing)
        .options(selectinload(Listing.images))
        .where(*filters)
        .order_by(Listing.is_premium.desc(), Listing.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    listings = (await db.execute(stmt)).scalars().unique().all()
    profiles = await owner_profiles(listings)
    favorite_ids = await favorite_listing_ids(db, user_id, [item.id for item in listings])

    return ListingSearchResponse(
        listings=[listing_to_card(item, profiles.get(item.owner_id), item.id in favorite_ids) for item in listings],
        total=total,
        page=page,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.get("/me", response_model=list[ListingCard])
async def get_my_listings(
    owner_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = (
        select(Listing)
        .options(selectinload(Listing.images))
        .where(Listing.owner_id == owner_id, Listing.status != ListingStatus.deleted)
        .order_by(Listing.created_at.desc())
    )
    listings = (await db.execute(stmt)).scalars().unique().all()
    profiles = await owner_profiles(listings)
    return [listing_to_card(item, profiles.get(item.owner_id)) for item in listings]


@router.get("/{id}/booking-info", response_model=ListingBookingInfo)
async def get_listing_booking_info(id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ListingBookingInfo:
    """Minimal listing data for the Order Service. Does not count as a view."""
    listing = await _load_listing(id, db)
    return ListingBookingInfo(
        id=listing.id,
        owner_id=listing.owner_id,
        title=listing.title,
        price=listing.price,
        status=listing.status,
        is_active=listing.is_active and not _ad_expired(listing),
        rental_type=rental_type_from_property_type(listing.property_type),
        available_spaces=listing.available_spaces,
        parent_listing_id=listing.parent_listing_id,
    )


@router.get("/{id}", response_model=ListingOut)
async def get_listing(
    id: uuid.UUID,
    user_id: Optional[int] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a listing by id and count the view. A signed-in user also learns whether they saved it."""
    await _load_listing(id, db)
    await db.execute(update(Listing).where(Listing.id == id).values(views_count=Listing.views_count + 1))
    await db.commit()
    listing = await _serialize(await _reload_listing(id, db))
    listing["is_favorite"] = bool(await favorite_listing_ids(db, user_id, [id]))
    return listing


@router.put("/{id}", response_model=ListingOut)
@router.patch("/{id}", response_model=ListingOut)
async def update_listing(
    id: uuid.UUID,
    payload: ListingUpdate,
    owner_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a listing (owner only)."""
    listing = await _get_owned_listing(id, owner_id, db)
    if listing.parent_listing_id is not None:
        locked = ROOMMATE_LOCKED_FIELDS & payload.model_fields_set
        if locked:
            raise HTTPException(
                status_code=UNPROCESSABLE_STATUS,
                detail=f"A roommate listing follows its apartment. Cannot change: {', '.join(sorted(locked))}.",
            )
        if payload.available_spaces is not None and not 1 <= payload.available_spaces <= MAX_ROOMMATE_SPACES:
            raise HTTPException(
                status_code=UNPROCESSABLE_STATUS, detail=f"Offer between 1 and {MAX_ROOMMATE_SPACES} places."
            )
    _apply_listing_payload(listing, payload, is_create=False)
    if payload.images is not None:
        _replace_images(listing, payload.images)
    await db.commit()

    updated = await _reload_listing(id, db)
    await publish_listing_event(LISTING_UPDATED, updated)
    return await _serialize(updated)


@router.delete("/{id}", response_model=ListingOut)
async def delete_listing(
    id: uuid.UUID,
    owner_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Soft-delete a listing (owner only)."""
    listing = await _get_owned_listing(id, owner_id, db)
    listing.status = ListingStatus.deleted
    listing.is_active = False
    await db.execute(
        update(Listing)
        .where(Listing.parent_listing_id == id, Listing.status != ListingStatus.deleted)
        .values(status=ListingStatus.archived, is_active=False)
    )
    await db.commit()

    deleted = await _reload_listing(id, db)
    await publish_listing_event(LISTING_UPDATED, deleted)
    return await _serialize(deleted)


@router.post("/{id}/activate-basic", response_model=ActivateListingResponse)
async def activate_basic_listing(
    id: uuid.UUID,
    owner_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ActivateListingResponse:
    listing = await _get_owned_listing(id, owner_id, db)
    listing.status = ListingStatus.active
    listing.is_active = True
    listing.is_premium = False
    listing.premium_expires_at = None
    await db.commit()
    return ActivateListingResponse(message="Listing activated as basic")


@router.post("/{id}/upgrade-to-premium", response_model=UpgradeToPremiumResponse)
async def upgrade_to_premium(
    id: uuid.UUID,
    owner_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UpgradeToPremiumResponse:
    listing = await _get_owned_listing(id, owner_id, db)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.premium_duration_days)
    listing.status = ListingStatus.active
    listing.is_active = True
    listing.is_premium = True
    listing.premium_expires_at = expires_at
    await db.commit()
    return UpgradeToPremiumResponse(message="Listing upgraded to premium", premium_expires_at=expires_at)


@router.post("/{id}/mark-occupied", response_model=ActivateListingResponse)
async def mark_occupied(
    id: uuid.UUID,
    owner_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ActivateListingResponse:
    listing = await _get_owned_listing(id, owner_id, db)
    listing.status = ListingStatus.rented
    listing.available_spaces = 0
    await db.commit()
    return ActivateListingResponse(message="Listing marked occupied")


@router.post("/{id}/mark-available", response_model=ActivateListingResponse)
async def mark_available(
    id: uuid.UUID,
    owner_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ActivateListingResponse:
    listing = await _get_owned_listing(id, owner_id, db)
    listing.status = ListingStatus.active
    listing.is_active = True
    listing.available_spaces = max(1, listing.available_spaces, listing.max_guests or 1)
    await db.commit()
    return ActivateListingResponse(message="Listing marked available")
