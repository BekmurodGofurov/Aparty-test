import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.review import Review
from app.models.listing import Listing
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter()


@router.post("/", response_model=ReviewOut)
async def create_review(
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Review:
    listing = await db.get(Listing, payload.listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    existing = await db.scalar(
        select(Review).where(
            Review.listing_id == payload.listing_id,
            Review.author_id == current_user.id,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail="Bu listing uchun sharh qoldirgansiz")
    review = Review(listing_id=payload.listing_id, author_id=current_user.id, rating=payload.rating, review_text=payload.review_text)
    db.add(review)
    await db.commit()
    created = await db.scalar(select(Review).options(selectinload(Review.author)).where(Review.id == review.id))
    if created is None:
        raise HTTPException(status_code=500, detail="Sharh yaratildi, lekin qayta yuklanmadi")
    return created


@router.get("/listing/{listing_id}", response_model=list[ReviewOut])
async def get_reviews_by_listing(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[Review]:
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.author))
        .where(Review.listing_id == listing_id)
        .order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())
