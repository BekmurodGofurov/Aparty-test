from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.apartments.models import Listing
from app.domains.orders.models import ListingPayment


async def create_listing(db: AsyncSession, listing: Listing) -> Listing:
    db.add(listing)
    await db.flush()
    return listing


async def create_listing_payment(db: AsyncSession, payment: ListingPayment) -> ListingPayment:
    db.add(payment)
    return payment


async def commit_listing(db: AsyncSession, listing: Listing) -> Listing:
    await db.commit()
    await db.refresh(listing)
    return listing
