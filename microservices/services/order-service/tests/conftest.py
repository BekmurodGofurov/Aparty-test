"""Shared fixtures. Tests run against a real PostgreSQL database named `*_test`."""

from __future__ import annotations

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")
if not TEST_DATABASE_URL.rsplit("/", 1)[-1].endswith("_test"):
    sys.exit("Set TEST_DATABASE_URL to a PostgreSQL database whose name ends with '_test'.")

TEST_JWT_SECRET = "test-only-jwt-secret-with-at-least-32-bytes"

os.environ.update(
    DATABASE_URL=TEST_DATABASE_URL,
    RABBITMQ_URL="amqp://rabbitmq.test",
    JWT_SECRET_KEY=TEST_JWT_SECRET,
    CATALOG_SERVICE_URL="http://catalog.test",
    IAM_SERVICE_URL="http://iam.test",
    CORS_ORIGINS="http://localhost:5173",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.clients.catalog import CatalogUnavailableError  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas import ListingBookingInfo, PublicProfile  # noqa: E402

OWNER_ID = 10
GUEST_ID = 20
PRICE_PER_NIGHT = 100000


def make_token(user_id: int | str, token_type: str = "access", secret: str = TEST_JWT_SECRET,
               role: str | None = "student", **overrides) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": str(user_id), "type": token_type, "role": role, "iss": "aparty-iam", "aud": "aparty-api",
              "iat": now, "exp": now + timedelta(minutes=5)}
    claims.update(overrides)
    return jwt.encode(claims, secret, algorithm="HS256")


def auth_headers(user_id: int, role: str | None = "student") -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id, role=role)}"}


def in_days(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


@pytest_asyncio.fixture(scope="session")
async def engine():
    test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(engine):
    yield
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE bookings"))


@pytest_asyncio.fixture
async def client(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def published_events(monkeypatch):
    events: list[tuple[str, dict]] = []

    async def fake_publish(routing_key, payload):
        events.append((routing_key, payload))

    monkeypatch.setattr("app.events.publish_event", fake_publish)
    return events


class FakeCatalog:
    """Stands in for the Catalog Service booking-info endpoint."""

    def __init__(self):
        self.listings: dict[uuid.UUID, ListingBookingInfo] = {}
        self.unavailable = False

    def add(self, owner_id: int = OWNER_ID, price: float = PRICE_PER_NIGHT, **overrides) -> uuid.UUID:
        listing = ListingBookingInfo(
            **{"id": uuid.uuid4(), "owner_id": owner_id, "title": "Test flat", "price": price, "status": "active", "is_active": True,
               "rental_type": "full_unit", "available_spaces": 1, **overrides}
        )
        self.listings[listing.id] = listing
        return listing.id

    async def fetch(self, listing_id):
        if self.unavailable:
            raise CatalogUnavailableError
        return self.listings.get(listing_id)


@pytest.fixture(autouse=True)
def iam_profiles(monkeypatch):
    """Requester profiles returned by the fake IAM client; empty means IAM has no data."""
    profiles: dict[int, PublicProfile] = {}

    async def fake_fetch(user_ids):
        return {uid: profiles[uid] for uid in set(user_ids) if uid in profiles}

    monkeypatch.setattr("app.routers.bookings.fetch_public_profiles", fake_fetch)
    return profiles


@pytest.fixture
def catalog(monkeypatch):
    fake = FakeCatalog()
    monkeypatch.setattr("app.routers.bookings.fetch_booking_info", fake.fetch)
    return fake


@pytest_asyncio.fixture
async def create_booking(client, catalog):
    async def _create(listing_id=None, guest_id: int = GUEST_ID, start: int = 5, end: int = 8, **overrides):
        listing_id = listing_id or catalog.add()
        response = await client.post(
            "/api/v1/bookings",
            json={"listing_id": str(listing_id), "start_date": in_days(start), "end_date": in_days(end), **overrides},
            headers=auth_headers(guest_id),
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _create
