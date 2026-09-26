from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import settings
from app.constants import DEFAULT_LATITUDE, DEFAULT_LONGITUDE

# Database connection options
connect_args = {
    "timeout": 60,
    "command_timeout": 60,
    "statement_cache_size": 0,
}

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Local/dev compatibility migration only.
        # create_all() does not alter existing tables, so these IF NOT EXISTS
        # statements keep old local Docker volumes usable while the service is
        # being split out. Production/Neon must use explicit Alembic migrations.
        await conn.execute(text("""
            DO $$
            BEGIN
                CREATE TYPE listing_target_gender AS ENUM ('male', 'female', 'mixed');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
        """))
        await conn.execute(text("""
            DO $$
            BEGIN
                CREATE TYPE listing_source AS ENUM ('owner', 'makler', 'exiting_student');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
        """))
        await conn.execute(text("ALTER TYPE listing_source ADD VALUE IF NOT EXISTS 'roommate'"))
        # `price_usd` was replaced by `price`; old local volumes still carry it as NOT NULL.
        await conn.execute(text("ALTER TABLE listings DROP COLUMN IF EXISTS price_usd"))
        await conn.execute(text(f"""
            ALTER TABLE listings
                ADD COLUMN IF NOT EXISTS region VARCHAR(100),
                ADD COLUMN IF NOT EXISTS district VARCHAR(100),
                ADD COLUMN IF NOT EXISTS address VARCHAR(255),
                ADD COLUMN IF NOT EXISTS building_number VARCHAR(20),
                ADD COLUMN IF NOT EXISTS room_number VARCHAR(20),
                ADD COLUMN IF NOT EXISTS floor INTEGER,
                ADD COLUMN IF NOT EXISTS total_floors INTEGER,
                ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION NOT NULL DEFAULT {DEFAULT_LATITUDE},
                ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION NOT NULL DEFAULT {DEFAULT_LONGITUDE},
                ADD COLUMN IF NOT EXISTS rooms_count INTEGER NOT NULL DEFAULT 1,
                ADD COLUMN IF NOT EXISTS area_m2 INTEGER,
                ADD COLUMN IF NOT EXISTS target_gender listing_target_gender NOT NULL DEFAULT 'mixed',
                ADD COLUMN IF NOT EXISTS source listing_source NOT NULL DEFAULT 'owner',
                ADD COLUMN IF NOT EXISTS max_guests INTEGER NOT NULL DEFAULT 1,
                ADD COLUMN IF NOT EXISTS available_spaces INTEGER NOT NULL DEFAULT 1,
                ADD COLUMN IF NOT EXISTS amenities JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                ADD COLUMN IF NOT EXISTS is_premium BOOLEAN NOT NULL DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS views_count INTEGER NOT NULL DEFAULT 0,
                ADD COLUMN IF NOT EXISTS parent_listing_id UUID,
                ADD COLUMN IF NOT EXISTS residents_male INTEGER,
                ADD COLUMN IF NOT EXISTS residents_female INTEGER,
                ADD COLUMN IF NOT EXISTS residents_children INTEGER,
                ADD COLUMN IF NOT EXISTS available_from DATE,
                ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_listings_parent_listing_id ON listings (parent_listing_id)"))
        # Earlier roommate design (booking-backed, owner permission), replaced by expiring ads.
        await conn.execute(text("DROP INDEX IF EXISTS uq_listings_active_tenancy"))
        await conn.execute(text(
            "ALTER TABLE listings DROP COLUMN IF EXISTS allow_roommates, "
            "DROP COLUMN IF EXISTS tenancy_booking_id, DROP COLUMN IF EXISTS tenancy_end_date"
        ))
