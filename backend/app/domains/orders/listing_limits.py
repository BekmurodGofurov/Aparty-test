from __future__ import annotations

from dataclasses import dataclass


TRIAL_MONTHS = 6

# User roles: guest, admin, broker, owner

@dataclass(frozen=True)
class ListingLimit:
    simple_limit: int
    premium_limit: int


def get_listing_limit_for_role(role_name: str) -> ListingLimit:
    """Get listing limits based on user role
    - guest: 0 simple, 0 premium
    - admin: 100 simple, 100 premium (no limits)
    - makler: 10 simple, 1 premium
    - owner: 1 simple, 1 premium
    """
    if role_name == "owner":
        return ListingLimit(simple_limit=1, premium_limit=1)
    if role_name == "makler":
        return ListingLimit(simple_limit=10, premium_limit=1)
    if role_name == "admin":
        return ListingLimit(simple_limit=100, premium_limit=100)
    # guest and others: no listings allowed
    return ListingLimit(simple_limit=0, premium_limit=0)
