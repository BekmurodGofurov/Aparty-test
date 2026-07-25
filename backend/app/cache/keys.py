"""Centralized cache key constants for Redis.

All cache keys MUST use the ``aparty:`` prefix to avoid collisions with
other services that might share the same Redis instance.
"""

from __future__ import annotations

CACHE_PREFIX: str = "aparty"
POPULAR_APARTMENTS_KEY: str = f"{CACHE_PREFIX}:apartments:popular"


def build_key(*parts: str) -> str:
    """Build a namespaced cache key: ``aparty:part1:part2:...``

    Args:
        *parts: Variable path segments appended after the global prefix.

    Returns:
        A colon-separated cache key string.

    Example::

        >>> build_key("listings", "detail", "abc-123")
        'aparty:listings:detail:abc-123'
    """
    return ":".join([CACHE_PREFIX, *parts])
