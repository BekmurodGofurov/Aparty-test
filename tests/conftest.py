"""Shared pytest fixtures for backend API tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

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
from app.utils.security import create_token, hash_password

# Allow PostgreSQL-specific column types to compile on SQLite for tests.
@compiles(UUID, "sqlite")
def _compile_uuid_sqlite(_type, _compiler, **_kw):
    return "CHAR(32)"


@compiles(ARRAY, "sqlite")
def _compile_array_sqlite(_type, _compiler, **_kw):
    return "TEXT"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, _compiler, **_kw):
    return "JSON"


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def disable_startup_migrations(monkeypatch):
    monkeypatch.setattr("app.config.settings.auto_migrate_on_startup", False)


@pytest_asyncio.fixture
async def db_engine():
    # SQLite cannot store PostgreSQL ARRAY columns; use JSON for image lists in tests.
    Listing.__table__.c.images.type = JSON()

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, db_engine) -> AsyncGenerator[AsyncClient, None]:
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
        full_name="Test Admin",
        phone="+998900000001",
        role=UserRole.admin,
        hashed_password=hash_password("password123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def owner_user(db_session: AsyncSession) -> User:
    user = User(
        full_name="Test Owner",
        phone="+998901234567",
        role=UserRole.owner,
        hashed_password=hash_password("password123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession) -> User:
    user = User(
        full_name="Test Student",
        phone="+998907654321",
        role=UserRole.student,
        hashed_password=hash_password("password123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def makler_user(db_session: AsyncSession) -> User:
    user = User(
        full_name="Test Makler",
        phone="+998901112233",
        role=UserRole.makler,
        hashed_password=hash_password("password123"),
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
            "washing_machine": False,
            "refrigerator": True,
            "kitchen_appliances": True,
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
