"""
Subscription update operations.

The ``try_consume_with_lock`` function is the authoritative way to decrement a
Makler's subscription slot.  It uses a SELECT … FOR UPDATE pessimistic lock so
that two concurrent requests cannot both pass the ``used_count < listing_limit``
check and both increment the counter — fixing the race condition.
"""

import uuid
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.orders.models import Subscription

from database.operations.select import subscriptions as select_subscriptions


async def deactivate(db: AsyncSession, subscription_id: uuid.UUID) -> Optional[Subscription]:
    sub = await select_subscriptions.get_by_id(db, subscription_id)
    if sub is None:
        return None
    sub.is_active = False
    await db.commit()
    await db.refresh(sub)
    return sub


async def increment_used_count(db: AsyncSession, subscription_id: uuid.UUID) -> Optional[Subscription]:
    sub = await select_subscriptions.get_by_id(db, subscription_id)
    if sub is None:
        return None
    sub.used_count += 1
    await db.commit()
    await db.refresh(sub)
    return sub


async def try_consume_with_lock(
    db: AsyncSession,
    user_id: int,
    today,  # datetime.date
) -> Optional[Subscription]:
    """Atomically consume one listing slot from the Makler's active subscription.

    Uses ``SELECT … FOR UPDATE`` to acquire a pessimistic row-level lock,
    preventing concurrent requests from both observing ``used_count <
    listing_limit`` and double-spending the same slot.

    Returns the updated :class:`Subscription` row on success, or ``None`` if no
    active subscription with remaining capacity exists.

    The caller is responsible for calling ``db.rollback()`` if they decide NOT
    to proceed with listing creation after this call returns ``None``.
    The caller must NOT commit before calling this function; the session must
    still be inside an active transaction so the lock is effective.
    """
    from datetime import date as _date

    stmt = (
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.is_active.is_(True),
            Subscription.start_date <= today,
            Subscription.end_date >= today,
            Subscription.used_count < Subscription.listing_limit,
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
        .with_for_update()  # ← pessimistic row-level lock
    )

    result = await db.execute(stmt)
    sub: Optional[Subscription] = result.scalar_one_or_none()

    if sub is None:
        # No eligible subscription — nothing to consume.
        return None

    # Safe to increment: the lock guarantees no other concurrent transaction
    # can see this row with the same used_count value.
    sub.used_count += 1
    await db.flush()  # push the UPDATE to the DB within this transaction;
                      # the lock is released only when the outer transaction commits.
    return sub
