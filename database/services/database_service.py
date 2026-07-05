from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from database.repositories import (
    UserRepository,
    ListingRepository,
    RentalRepository,
    PaymentRepository,
    ReviewRepository,
    SubscriptionRepository,
)


class DatabaseService:
    """Database service providing access to all repositories - Async"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._user_repo: UserRepository | None = None
        self._listing_repo: ListingRepository | None = None
        self._rental_repo: RentalRepository | None = None
        self._payment_repo: PaymentRepository | None = None
        self._review_repo: ReviewRepository | None = None
        self._subscription_repo: SubscriptionRepository | None = None

    @property
    def users(self) -> UserRepository:
        if self._user_repo is None:
            self._user_repo = UserRepository(self.session)
        return self._user_repo

    @property
    def listings(self) -> ListingRepository:
        if self._listing_repo is None:
            self._listing_repo = ListingRepository(self.session)
        return self._listing_repo

    @property
    def rentals(self) -> RentalRepository:
        if self._rental_repo is None:
            self._rental_repo = RentalRepository(self.session)
        return self._rental_repo

    @property
    def payments(self) -> PaymentRepository:
        if self._payment_repo is None:
            self._payment_repo = PaymentRepository(self.session)
        return self._payment_repo

    @property
    def reviews(self) -> ReviewRepository:
        if self._review_repo is None:
            self._review_repo = ReviewRepository(self.session)
        return self._review_repo

    @property
    def subscriptions(self) -> SubscriptionRepository:
        if self._subscription_repo is None:
            self._subscription_repo = SubscriptionRepository(self.session)
        return self._subscription_repo

    async def commit(self):
        """Commit changes"""
        await self.session.commit()

    async def rollback(self):
        """Rollback changes"""
        await self.session.rollback()

    async def close(self):
        """Close session"""
        await self.session.close()


@asynccontextmanager
async def get_database_service() -> AsyncGenerator[DatabaseService, None]:
    """Context manager for database service"""
    async with AsyncSessionLocal() as session:
        try:
            db_service = DatabaseService(session)
            yield db_service
            await db_service.commit()
        except Exception:
            await db_service.rollback()
            raise

