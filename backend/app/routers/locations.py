"""Locations router — static metadata (regions, amenities, metro stations)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from app.cache import STATIC_DATA_JITTER, STATIC_DATA_TTL, cached, etag

router = APIRouter()


@router.get("")
@router.get("/")
@etag
@cached(
    key_template="aparty:locations:all",
    ttl=STATIC_DATA_TTL,
    jitter_range=STATIC_DATA_JITTER,
)
async def get_locations(request: Request) -> dict:
    """Return static metadata (regions, amenities, metro stations).

    Cached for 24 hours (86,400s) with 2 hours (7,200s) jitter window.

    Decorator stack (top → bottom execution order):
        1. ``@etag``   — Checks ``If-None-Match``; returns 304 if data unchanged.
        2. ``@cached`` — Serves from Redis if available; falls to DB on miss.

    This means on a warm cache + matching ETag, the client gets a 304 with
    **zero bytes** transferred and no database query at all.
    """
    return {
        "regions": [
            "Toshkent shahri",
            "Andijon viloyati",
            "Farg'ona viloyati",
            "Namangan viloyati",
            "Samarqand viloyati",
            "Buxoro viloyati",
        ],
        "metro_stations": [
            "Amir Temur Xiyoboni",
            "Chorsu",
            "Yunusobod",
            "Buyuk Ipak Yo'li",
            "Paxtakor",
        ],
        "amenities": [
            {"id": "wifi", "name": "Wi-Fi"},
            {"id": "ac", "name": "Konditsioner"},
            {"id": "washer", "name": "Kir yuvish mashinasi"},
            {"id": "tv", "name": "Televizor"},
            {"id": "fridge", "name": "Muzlatgich"},
        ],
    }
