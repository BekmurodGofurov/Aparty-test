import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut
from database.operations.insert import reviews as insert_reviews
from database.operations.select import listings as select_listings
from database.operations.select import reviews as select_reviews

router = APIRouter()


@router.post("/", response_model=ReviewOut)
async def create_review(
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Review:
    listing = await select_listings.get_by_id(db, payload.listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing topilmadi")
    existing = await select_reviews.get_by_listing_and_author(db, payload.listing_id, current_user.id)
    if existing is not None:
        raise HTTPException(status_code=400, detail="Bu listing uchun sharh qoldirgansiz")
    review = Review(
        listing_id=payload.listing_id,
        author_id=current_user.id,
        rating=payload.rating,
        review_text=payload.review_text,
    )
    created = await insert_reviews.create(db, review)
    if created is None:
        raise HTTPException(status_code=500, detail="Sharh yaratildi, lekin qayta yuklanmadi")
    return created


@router.get("/listing/{listing_id}", response_model=list[ReviewOut])
async def get_reviews_by_listing(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[Review]:
    return await select_reviews.get_by_listing_with_author(db, listing_id)
