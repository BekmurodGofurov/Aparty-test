from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_size=5, max_overflow=10, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables. Production schema changes must go through explicit migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Local/dev compatibility migration only: create_all() does not alter existing tables.
        await conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS apartment_listing_id UUID"))
        await conn.execute(text("UPDATE bookings SET apartment_listing_id = listing_id WHERE apartment_listing_id IS NULL"))
        await conn.execute(text("ALTER TABLE bookings ALTER COLUMN apartment_listing_id SET NOT NULL"))
        await conn.execute(text(
            "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS is_roommate_request BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        await conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS listing_title VARCHAR(255)"))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_bookings_apartment_listing_id ON bookings (apartment_listing_id)"
        ))
