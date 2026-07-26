"""Cache infrastructure for the Aparty platform."""

from __future__ import annotations

from app.core.cache.config import (
    DETAIL_PAGE_JITTER,
    DETAIL_PAGE_TTL,
    HEAVY_SEARCH_JITTER,
    HEAVY_SEARCH_TTL,
    STATIC_DATA_JITTER,
    STATIC_DATA_TTL,
    CachePolicies,
    CachePolicy,
)
from app.core.cache.etag import etag
from app.core.cache.keys import POPULAR_APARTMENTS_KEY, build_key
from app.core.cache.manager import CacheManager, cached

__all__ = [
    "CacheManager",
    "cached",
    "etag",
    "build_key",
    "POPULAR_APARTMENTS_KEY",
    "CachePolicies",
    "CachePolicy",
    "STATIC_DATA_TTL",
    "STATIC_DATA_JITTER",
    "HEAVY_SEARCH_TTL",
    "HEAVY_SEARCH_JITTER",
    "DETAIL_PAGE_TTL",
    "DETAIL_PAGE_JITTER",
]
