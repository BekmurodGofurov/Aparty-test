"""Apartments router — cached endpoints for apartment discovery and search."""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import (
    DETAIL_PAGE_JITTER,
    DETAIL_PAGE_TTL,
    HEAVY_SEARCH_JITTER,
    HEAVY_SEARCH_TTL,
    POPULAR_APARTMENTS_KEY,
    CacheManager,
    cached,
)
from app.database import get_db
from app.models.listing import Listing
from app.schemas.apartments import PopularApartmentItem, PopularApartmentsResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. Static/Popular Data Endpoint
# ---------------------------------------------------------------------------

@router.get("/popular", response_model=PopularApartmentsResponse)
async def get_popular_apartments(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return the top-20 most-viewed active listings.

    Uses explicit cache-aside with CacheManager.
    """
    redis = request.app.state.redis
    cache = CacheManager(redis)

    cached_data = await cache.get(POPULAR_APARTMENTS_KEY)
    if cached_data is not None:
        response = PopularApartmentsResponse(
            apartments=cached_data,
            total=len(cached_data),
            cached=True,
        )
        return JSONResponse(
            content=response.model_dump(mode="json"),
            headers={"X-Cache": "HIT"},
        )

    stmt = (
        select(Listing)
        .where(Listing.is_active == True)  # noqa: E712
        .order_by(Listing.views_count.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    listings = result.scalars().all()

    apartments = [
        PopularApartmentItem.model_validate(listing) for listing in listings
    ]
    apartments_json = [apt.model_dump(mode="json") for apt in apartments]

    await cache.set(
        POPULAR_APARTMENTS_KEY,
        apartments_json,
        ttl=HEAVY_SEARCH_TTL,
        jitter_range=HEAVY_SEARCH_JITTER,
    )

    response = PopularApartmentsResponse(
        apartments=apartments_json,
        total=len(apartments_json),
        cached=False,
    )
    return JSONResponse(
        content=response.model_dump(mode="json"),
        headers={"X-Cache": "MISS"},
    )


# ---------------------------------------------------------------------------
# 2. Heavy Search Endpoint (Query Params + Filter Results)
# ---------------------------------------------------------------------------

@router.get("/search")
@cached(
    key_template="aparty:apartments:search",
    ttl=HEAVY_SEARCH_TTL,
    jitter_range=HEAVY_SEARCH_JITTER,
)
async def search_apartments(
    request: Request,
    region: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    rooms_count: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Heavy search with filters.

    Cached for 5 mins (300s) with 1 min (60s) jitter window.
    The @cached decorator automatically constructs a unique cache key incorporating
    the sorted query parameters.
    """
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
    return {
        "results": items,
        "total": len(items),
    }


# ---------------------------------------------------------------------------
# 3. Detail Page Endpoint (Single Apartment Full Details)
# ---------------------------------------------------------------------------

@router.get("/{apartment_id}")
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
    """Single apartment detail page.

    Cached for 30 mins (1,800s) with 5 mins (300s) jitter window.
    The @cached decorator interpolates `{apartment_id}` into the cache key.
    """
    stmt = select(Listing).where(Listing.id == apartment_id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apartment not found",
        )

    return PopularApartmentItem.model_validate(listing).model_dump(mode="json")


# ---------------------------------------------------------------------------
# 4. Cache Management Endpoint
# ---------------------------------------------------------------------------

@router.delete("/popular/cache")
async def invalidate_popular_cache(
    request: Request,
) -> dict[str, str]:
    """Manually invalidate the popular apartments cache."""
    redis = request.app.state.redis
    cache = CacheManager(redis)
    await cache.delete(POPULAR_APARTMENTS_KEY)
    return {"status": "invalidated"}
