import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.listing import Listing
from app.models.payment import Payment
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.listing import ListingOut
from app.schemas.user import UserOut
from app.services.listing_limits import get_listing_limit_for_role

# role=admin
router = APIRouter(dependencies=[Depends(require_roles("admin"))])


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "university": user.university,
        "profile_picture_url": user.profile_picture_url,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
    }


def _listing_payload(listing: Listing, reviews_count: int = 0) -> dict:
    return {
        "id": listing.id,
        "owner_id": listing.owner_id,
        "region": listing.region,
        "district": listing.district,
        "address": listing.address,
        "rooms_count": listing.rooms_count,
        "area_m2": listing.area_m2,
        "price_usd": listing.price_usd,
        "target_gender": listing.target_gender,
        "source": listing.source,
        "available_spaces": listing.available_spaces,
        "is_premium": listing.is_premium,
        "premium_expires_at": listing.premium_expires_at,
        "is_active": listing.is_active,
        "views_count": listing.views_count,
        "description": listing.description,
        "images": listing.images or [],
        "created_at": listing.created_at,
        "reviews_count": reviews_count,
    }


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)) -> dict:
    users_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    listings_count = (await db.execute(select(func.count(Listing.id)))).scalar_one()
    revenue = (await db.execute(select(func.coalesce(func.sum(Payment.amount), 0)))).scalar_one()
    verified_users = (
        await db.execute(select(func.count(User.id)).where(User.is_verified.is_(True)))
    ).scalar_one()
    role_rows = (
        await db.execute(
            select(User.role, func.count(User.id))
            .group_by(User.role)
        )
    ).all()

    role_limits = {
        role_name: {
            "simple": get_listing_limit_for_role(role_name).simple_limit,
            "premium": get_listing_limit_for_role(role_name).premium_limit,
        }
        for role_name in ("owner", "makler", "admin")
    }

    return {
        "users": users_count,
        "verified_users": verified_users,
        "listings": listings_count,
        "revenue": float(revenue or 0),
        "complaints": 0,
        "role_counts": {role.value if role else "student": count for role, count in role_rows},
        "limits": role_limits,
    }


@router.get("/users", response_model=list[UserOut])
async def all_users(db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all())


@router.get("/users/{user_id}/detail")
async def user_detail(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    review_counts = (
        select(Review.listing_id, func.count(Review.id).label("reviews_count"))
        .group_by(Review.listing_id)
        .subquery()
    )
    rows = await db.execute(
        select(Listing, func.coalesce(review_counts.c.reviews_count, 0))
        .outerjoin(review_counts, review_counts.c.listing_id == Listing.id)
        .where(Listing.owner_id == user.id)
        .order_by(Listing.created_at.desc())
    )
    listings = [_listing_payload(listing, int(reviews_count or 0)) for listing, reviews_count in rows.all()]

    return {
        "user": _user_payload(user),
        "listings": listings,
        "listings_count": len(listings),
    }


@router.patch("/users/{user_id}/status")
async def set_user_status(user_id: uuid.UUID, payload: dict, db: AsyncSession = Depends(get_db)) -> dict:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    if user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Admin statusini bu yerdan o'zgartirib bo'lmaydi")

    user.is_verified = bool(payload.get("is_verified"))
    await db.commit()
    await db.refresh(user)
    return {"user": _user_payload(user)}


@router.get("/listings", response_model=list[ListingOut])
async def all_listings(db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(Listing).order_by(Listing.created_at.desc()))).scalars().all())


@router.get("/listings/{listing_id}/detail")
async def listing_detail(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")

    owner = await db.scalar(select(User).where(User.id == listing.owner_id))
    review_rows = await db.execute(
        select(Review, User)
        .join(User, User.id == Review.author_id)
        .where(Review.listing_id == listing.id)
        .order_by(Review.created_at.desc())
    )
    reviews = [
        {
            "id": review.id,
            "listing_id": review.listing_id,
            "author_id": review.author_id,
            "author_name": author.full_name,
            "author_phone": author.phone,
            "rating": review.rating,
            "text": review.review_text,
            "created_at": review.created_at,
        }
        for review, author in review_rows.all()
    ]

    return {
        "listing": _listing_payload(listing, len(reviews)),
        "owner": _user_payload(owner) if owner else None,
        "reviews": reviews,
        "reviews_count": len(reviews),
    }


@router.patch("/listings/{listing_id}/status")
async def set_listing_status(listing_id: uuid.UUID, payload: dict, db: AsyncSession = Depends(get_db)) -> dict:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")

    listing.is_active = bool(payload.get("is_active"))
    await db.commit()
    await db.refresh(listing)
    reviews_count = await db.scalar(select(func.count(Review.id)).where(Review.listing_id == listing.id))
    return {"listing": _listing_payload(listing, int(reviews_count or 0))}


@router.delete("/reviews/{review_id}", status_code=204)
async def delete_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    review = await db.scalar(select(Review).where(Review.id == review_id))
    if review is None:
        raise HTTPException(status_code=404, detail="Comment topilmadi")

    await db.delete(review)
    await db.commit()
    return None
