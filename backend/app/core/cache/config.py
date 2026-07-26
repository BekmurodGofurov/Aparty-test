"""Cache TTL and Jitter policy configuration constants.

To prevent cache stampedes (thundering herd problem), every cached resource
category is assigned a base TTL and a Jitter window.
Effective TTL is computed as:
    effective_ttl = base_ttl + random.uniform(-jitter, +jitter)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CachePolicy:
    """Dataclass holding TTL and Jitter configuration for a cache strategy."""

    ttl: int
    jitter: int


# ---------------------------------------------------------------------------
# Cache Policy Constants (values in seconds)
# ---------------------------------------------------------------------------

# Static Data: Regions, Amenities, Metro stations
# TTL = 24 hours (86,400s), Jitter = 2 hours (7,200s)
STATIC_DATA_TTL: int = 86400
STATIC_DATA_JITTER: int = 7200

# Heavy Search: Apartment listings, Filter results
# TTL = 5 mins (300s), Jitter = 1 min (60s)
HEAVY_SEARCH_TTL: int = 300
HEAVY_SEARCH_JITTER: int = 60

# Detail Page: Single apartment full details
# TTL = 30 mins (1,800s), Jitter = 5 mins (300s)
DETAIL_PAGE_TTL: int = 1800
DETAIL_PAGE_JITTER: int = 300


# ---------------------------------------------------------------------------
# Structured Cache Policies Object
# ---------------------------------------------------------------------------


class CachePolicies:
    """Structured container providing ergonomic access to predefined cache policies."""

    STATIC_DATA = CachePolicy(ttl=STATIC_DATA_TTL, jitter=STATIC_DATA_JITTER)
    HEAVY_SEARCH = CachePolicy(ttl=HEAVY_SEARCH_TTL, jitter=HEAVY_SEARCH_JITTER)
    DETAIL_PAGE = CachePolicy(ttl=DETAIL_PAGE_TTL, jitter=DETAIL_PAGE_JITTER)
