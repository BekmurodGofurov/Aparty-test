"""Conversions between Listing ORM objects and API/event representations."""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

from app.clients.iam import PublicProfile
from app.constants import ROLE_MAKLER, TELEGRAM_LINK_BASE
from app.models import Listing, ListingSource
from app.schemas import ListingCard, RentalType

SHARED_PROPERTY_TYPES = frozenset({"shared_room", "shared"})
STUDENT_SOURCES = (ListingSource.roommate, ListingSource.exiting_student)


def rental_type_from_property_type(property_type: Optional[str]) -> RentalType:
    return RentalType.shared_room if property_type in SHARED_PROPERTY_TYPES else RentalType.full_unit


def property_type_from_rental_type(rental_type: Optional[RentalType]) -> str:
    return (rental_type or RentalType.full_unit).value


def source_for_role(role: str) -> ListingSource:
    """The listing source is derived from the creator's role, never from the request."""
    return ListingSource.makler if role == ROLE_MAKLER else ListingSource.owner


def owner_role(listing: Listing) -> str:
    if listing.source == ListingSource.makler:
        return "makler"
    if listing.source in STUDENT_SOURCES:
        return "student"
    return "owner"


def telegram_url(owner: Optional[PublicProfile]) -> Optional[str]:
    """Link to the owner's Telegram chat, or None when they have no username."""
    if owner is None or not owner.telegram_username:
        return None
    return f"{TELEGRAM_LINK_BASE}{quote(owner.telegram_username, safe='')}"


def listing_image_urls(listing: Listing) -> list[str]:
    """Image URLs with the primary image first."""
    images = sorted(listing.images, key=lambda image: (not image.is_primary, str(image.id)))
    return [image.image_url for image in images]


def listing_to_out(listing: Listing, owner: Optional[PublicProfile] = None) -> dict[str, Any]:
    return {
        "id": listing.id,
        "owner_id": listing.owner_id,
        "title": listing.title,
        "description": listing.description,
        "price": listing.price,
        "rental_type": rental_type_from_property_type(listing.property_type),
        "status": listing.status,
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
        "target_gender": listing.target_gender,
        "source": listing.source,
        "max_guests": listing.max_guests,
        "available_spaces": listing.available_spaces,
        "amenities": listing.amenities or {},
        "images": listing_image_urls(listing),
        "is_premium": listing.is_premium,
        "premium_expires_at": listing.premium_expires_at,
        "is_active": listing.is_active,
        "views_count": listing.views_count,
        "parent_listing_id": listing.parent_listing_id,
        "residents_male": listing.residents_male,
        "residents_female": listing.residents_female,
        "residents_children": listing.residents_children,
        "available_from": listing.available_from,
        "expires_at": listing.expires_at,
        "owner_full_name": owner.full_name if owner else "",
        "owner_phone": owner.phone if owner else None,
        "owner_telegram_url": telegram_url(owner),
        "owner_role": owner_role(listing),
        "owner_verified": owner.is_verified if owner else False,
        "rating": None,
        "reviews_count": 0,
        "created_at": listing.created_at,
        "updated_at": listing.updated_at,
    }


def listing_to_card(
    listing: Listing, owner: Optional[PublicProfile] = None, is_favorite: bool = False
) -> dict[str, Any]:
    full = listing_to_out(listing, owner)
    card = {field: full[field] for field in ListingCard.model_fields if field != "is_favorite"}
    card["is_favorite"] = is_favorite
    return card
