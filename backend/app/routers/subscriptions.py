import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.subscription import Subscription
from app.models.subscription import SubscriptionType
from app.models.user import User, UserRole
from app.schemas.subscription import SubscriptionOut, SubscriptionPurchase

router = APIRouter()


@router.get("/me", response_model=list[SubscriptionOut])
async def get_my_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Subscription]:
    result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id).order_by(Subscription.created_at.desc()))
    return list(result.scalars().all())


@router.post("/purchase", response_model=SubscriptionOut)
async def purchase_subscription(
    payload: SubscriptionPurchase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Subscription:
    subscription = Subscription(user_id=current_user.id, **payload.model_dump())
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.post("/{plan_id}", response_model=SubscriptionOut)
async def purchase_subscription_by_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Subscription:
    plans = {
        "free": (SubscriptionType.makler_s, 5, 30),
        "s": (SubscriptionType.makler_s, 25, 30),
        "l": (SubscriptionType.makler_l, 100, 30),
    }
    if plan_id not in plans:
        raise HTTPException(status_code=404, detail="Plan topilmadi")

    sub_type, limit, days = plans[plan_id]
    today = date.today()
    subscription = Subscription(
        user_id=current_user.id,
        type=sub_type,
        start_date=today,
        end_date=today + timedelta(days=days),
        listing_limit=limit,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.patch("/{subscription_id}/cancel", response_model=SubscriptionOut)
async def cancel_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Subscription:
    result = await db.execute(select(Subscription).where(Subscription.id == subscription_id))
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription topilmadi")
    if subscription.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Bu subscriptionni bekor qilishga ruxsat yo'q")
    subscription.is_active = False
    await db.commit()
    await db.refresh(subscription)
    return subscription
