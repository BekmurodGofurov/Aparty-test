import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.listing import Listing
from app.models.user import User, UserRole
from app.schemas.listing import ListingOut
from app.schemas.user import UserOut
from app.services.listing_limits import get_listing_limit_for_role
from database.operations.delete import reviews as delete_reviews
from database.operations.select import listings as select_listings
from database.operations.select import payments as select_payments
from database.operations.select import reviews as select_reviews
from database.operations.select import users as select_users
from database.operations.update import listings as update_listings
from database.operations.update import users as update_users

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
    users_count = await select_users.count_all(db)
    listings_count = await select_listings.count_all(db)
    revenue = await select_payments.sum_total_revenue(db)
    verified_users = await select_users.count_verified(db)
    role_rows = await select_users.count_by_role(db)

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
        "revenue": revenue,
        "complaints": 0,
        "role_counts": {role.value if role else "student": count for role, count in role_rows},
        "limits": role_limits,
    }


@router.get("/users", response_model=list[UserOut])
async def all_users(db: AsyncSession = Depends(get_db)):
    return await select_users.get_all(db)


@router.get("/users/{user_id}/detail")
async def user_detail(user_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    user = await select_users.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    listing_rows = await select_listings.get_owner_listings_with_review_counts(db, user.id)
    listings = [_listing_payload(listing, reviews_count) for listing, reviews_count in listing_rows]

    return {
        "user": _user_payload(user),
        "listings": listings,
        "listings_count": len(listings),
    }


@router.patch("/users/{user_id}/status")
async def set_user_status(user_id: int, payload: dict, db: AsyncSession = Depends(get_db)) -> dict:
    user = await select_users.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    if user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Admin statusini bu yerdan o'zgartirib bo'lmaydi")

    updated = await update_users.set_verified(db, user_id, is_verified=bool(payload.get("is_verified")))
    if updated is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return {"user": _user_payload(updated)}


@router.get("/listings", response_model=list[ListingOut])
async def all_listings(db: AsyncSession = Depends(get_db)):
    return await select_listings.get_all(db)


@router.get("/listings/{listing_id}/detail")
async def listing_detail(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    listing = await select_listings.get_by_id(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")

    owner = await select_users.get_by_id(db, listing.owner_id)
    review_rows = await select_reviews.get_listing_reviews_with_authors(db, listing.id)
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
        for review, author in review_rows
    ]

    return {
        "listing": _listing_payload(listing, len(reviews)),
        "owner": _user_payload(owner) if owner else None,
        "reviews": reviews,
        "reviews_count": len(reviews),
    }


@router.patch("/listings/{listing_id}/status")
async def set_listing_status(listing_id: uuid.UUID, payload: dict, db: AsyncSession = Depends(get_db)) -> dict:
    listing = await select_listings.get_by_id(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")

    updated = await update_listings.set_active_status(db, listing, is_active=bool(payload.get("is_active")))
    reviews_count = await select_reviews.count_by_listing(db, listing.id)
    return {"listing": _listing_payload(updated, reviews_count)}


@router.delete("/reviews/{review_id}", status_code=204)
async def delete_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    review = await select_reviews.get_by_id(db, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Comment topilmadi")

    await delete_reviews.delete(db, review)
    return None
