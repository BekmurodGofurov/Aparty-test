import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import Favorite
from app.models.listing import Listing
from app.models.listing_payment import ListingPayment
from app.models.rental import RentalRequest, RentalRequestMessage
from app.models.review import Review


async def delete_listing(db: AsyncSession, listing: Listing) -> None:
    request_ids = select_request_ids_subquery(listing.id)
    await db.execute(delete(RentalRequestMessage).where(RentalRequestMessage.request_id.in_(request_ids)))
    await db.execute(delete(RentalRequest).where(RentalRequest.listing_id == listing.id))
    await db.execute(delete(Favorite).where(Favorite.listing_id == listing.id))
    await db.execute(delete(Review).where(Review.listing_id == listing.id))
    await db.execute(delete(ListingPayment).where(ListingPayment.listing_id == listing.id))
    await db.delete(listing)
    await db.commit()


def select_request_ids_subquery(listing_id: uuid.UUID):
    from sqlalchemy import select

    return select(RentalRequest.id).where(RentalRequest.listing_id == listing_id)
