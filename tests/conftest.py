"""Shared pytest fixtures for backend API tests."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import (  # noqa: F401
    favorite,
    listing,
    listing_payment,
    notification,
    payment,
    rental,
    review,
    subscription,
    user,
)
from app.models.listing import Listing, ListingSource, ListingTargetGender
from app.models.user import User, UserRole
from app.utils.security import create_token

# Use a test PostgreSQL database for accurate FOR UPDATE pessimistic locking and BigInts
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://bekmurod@localhost:5432/aparty_test"
)


@pytest.fixture(autouse=True)
def disable_startup_migrations(monkeypatch):
    monkeypatch.setattr("app.config.settings.auto_migrate_on_startup", False)


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Wipe and migrate using metadata (simulates alembic upgrade head for tests)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

@pytest_asyncio.fixture
async def mock_redis():
    """Mock the global Redis instance to test cache hits and misses."""
    with patch("app.main.redis") as mock_redis_client:
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis_client.set = AsyncMock()
        mock_redis_client.delete = AsyncMock()
        mock_redis_client.expire = AsyncMock()
        
        # Initialize FastAPICache to avoid 'You must call init first!' errors and pipeline errors
        FastAPICache.init(InMemoryBackend(), prefix="test-cache")
        
        yield mock_redis_client


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, db_engine, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("app.database.engine", db_engine),
        patch("app.main.premium_expiry_loop", new=AsyncMock()),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        id=98765432101,  # BigInteger
        full_name="Test Admin",
        phone="+998900000001",
        role=UserRole.admin,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def owner_user(db_session: AsyncSession) -> User:
    user = User(
        id=98765432102,  # BigInteger
        full_name="Test Owner",
        phone="+998901234567",
        role=UserRole.owner,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession) -> User:
    user = User(
        id=98765432103,  # BigInteger
        full_name="Test Student",
        phone="+998907654321",
        role=UserRole.student,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def makler_user(db_session: AsyncSession) -> User:
    user = User(
        id=98765432104,  # BigInteger
        full_name="Test Makler",
        phone="+998901112233",
        role=UserRole.makler,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_token(str(user.id), expires_minutes=30)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_listing_payload() -> dict:
    return {
        "region": "Toshkent shahri",
        "district": "Yunusobod",
        "address": "Test Street 1",
        "latitude": 41.3111,
        "longitude": 69.2797,
        "rooms_count": 2,
        "area_m2": 55,
        "price_usd": 300,
        "target_gender": "mixed",
        "max_guests": 3,
        "available_spaces": 2,
        "amenities": {
            "wifi": True,
            "gas": True,
            "water": True,
            "tv": False,
            "ac": True,
            "washer": False,
            "fridge": True,
            "kitchenware": True,
        },
        "images": ["https://example.com/image1.jpg"],
        "description": "Test listing",
        "is_premium": False,
    }


@pytest_asyncio.fixture
async def active_listing(db_session: AsyncSession, makler_user: User) -> Listing:
    listing = Listing(
        owner_id=makler_user.id,
        region="Toshkent shahri",
        district="Yunusobod",
        address="Active Listing Street",
        latitude=41.3111,
        longitude=69.2797,
        rooms_count=2,
        area_m2=50,
        price_usd=250,
        target_gender=ListingTargetGender.mixed,
        source=ListingSource.makler,
        max_guests=3,
        available_spaces=2,
        amenities={"wifi": True, "gas": True},
        images=["https://example.com/active.jpg"],
        description="Active test listing",
        is_premium=False,
        is_active=True,
        views_count=10,
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)
    return listing
