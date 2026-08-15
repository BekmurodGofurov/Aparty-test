"""Catalog Service Listings Router (`/api/v1/listings`)."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Listing, ListingImage, ListingStatus
from app.rabbitmq import publish_event
from app.schemas import ListingCreate, ListingOut, ListingUpdate
from app.security import get_current_owner_id

router = APIRouter(prefix="/api/v1/listings", tags=["Listings"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ListingOut)
async def create_listing(
    payload: ListingCreate,
    owner_id: int = Depends(get_current_owner_id),
    db: AsyncSession = Depends(get_db),
) -> ListingOut:
    """Yangi e'lon yaratish (rasmlar URL-manzillari ro'yxati bilan birga)."""
    new_listing = Listing(
        owner_id=owner_id,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        property_type=payload.property_type,
        status=ListingStatus.active,
    )
    db.add(new_listing)
    await db.flush()

    for img_data in payload.images:
        image_record = ListingImage(
            listing_id=new_listing.id,
            image_url=img_data.image_url,
            delete_url=img_data.delete_url,
            is_primary=img_data.is_primary,
        )
        db.add(image_record)

    await db.commit()

    # Re-query with loaded images relationship
    stmt = select(Listing).options(selectinload(Listing.images)).where(Listing.id == new_listing.id)
    result = await db.execute(stmt)
    created_listing = result.scalar_one()

    # Publish RabbitMQ event
    event_payload = {
        "event": "listing.created",
        "id": str(created_listing.id),
        "owner_id": created_listing.owner_id,
        "title": created_listing.title,
        "description": created_listing.description,
        "price": created_listing.price,
        "property_type": created_listing.property_type,
        "status": created_listing.status.value,
        "images": [img.image_url for img in created_listing.images],
    }
    await publish_event("listing.created", event_payload)

    return created_listing


@router.get("/{id}", response_model=ListingOut)
async def get_listing(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ListingOut:
    """ID bo'yicha e'lon ma'lumotlarini olish."""
    stmt = select(Listing).options(selectinload(Listing.images)).where(Listing.id == id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing or listing.status == ListingStatus.deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E'lon topilmadi.",
        )

    return listing


@router.put("/{id}", response_model=ListingOut)
@router.patch("/{id}", response_model=ListingOut)
async def update_listing(
    id: uuid.UUID,
    payload: ListingUpdate,
    owner_id: int = Depends(get_current_owner_id),
    db: AsyncSession = Depends(get_db),
) -> ListingOut:
    """E'lon va uning statusini tahrirlash (faqat e'lon egasi uchun)."""
    stmt = select(Listing).options(selectinload(Listing.images)).where(Listing.id == id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing or listing.status == ListingStatus.deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E'lon topilmadi.",
        )

    if listing.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat e'lon egasi tahrirlashi mumkin.",
        )

    if payload.title is not None:
        listing.title = payload.title
    if payload.description is not None:
        listing.description = payload.description
    if payload.price is not None:
        listing.price = payload.price
    if payload.property_type is not None:
        listing.property_type = payload.property_type
    if payload.status is not None:
        listing.status = payload.status

    if payload.images is not None:
        # Replace existing images with new ones if supplied
        listing.images.clear()
        for img_data in payload.images:
            image_record = ListingImage(
                listing_id=listing.id,
                image_url=img_data.image_url,
                delete_url=img_data.delete_url,
                is_primary=img_data.is_primary,
            )
            listing.images.append(image_record)

    await db.commit()

    # Re-query
    stmt = select(Listing).options(selectinload(Listing.images)).where(Listing.id == id)
    result = await db.execute(stmt)
    updated_listing = result.scalar_one()

    # Publish RabbitMQ event
    event_payload = {
        "event": "listing.updated",
        "id": str(updated_listing.id),
        "owner_id": updated_listing.owner_id,
        "title": updated_listing.title,
        "description": updated_listing.description,
        "price": updated_listing.price,
        "property_type": updated_listing.property_type,
        "status": updated_listing.status.value,
        "images": [img.image_url for img in updated_listing.images],
    }
    await publish_event("listing.updated", event_payload)

    return updated_listing


@router.delete("/{id}", response_model=ListingOut)
async def delete_listing(
    id: uuid.UUID,
    owner_id: int = Depends(get_current_owner_id),
    db: AsyncSession = Depends(get_db),
) -> ListingOut:
    """E'lonni o'chirish (statusini 'deleted' ga o'tkazish, faqat e'lon egasi uchun)."""
    stmt = select(Listing).options(selectinload(Listing.images)).where(Listing.id == id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing or listing.status == ListingStatus.deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E'lon topilmadi.",
        )

    if listing.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat e'lon egasi o'chirishi mumkin.",
        )

    listing.status = ListingStatus.deleted
    await db.commit()

    # Re-query
    stmt = select(Listing).options(selectinload(Listing.images)).where(Listing.id == id)
    result = await db.execute(stmt)
    deleted_listing = result.scalar_one()

    # Publish RabbitMQ event
    event_payload = {
        "event": "listing.updated",
        "id": str(deleted_listing.id),
        "owner_id": deleted_listing.owner_id,
        "status": ListingStatus.deleted.value,
    }
    await publish_event("listing.updated", event_payload)

    return deleted_listing
