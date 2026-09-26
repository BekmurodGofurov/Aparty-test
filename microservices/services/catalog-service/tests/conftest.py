"""Shared fixtures. Tests run against a real PostgreSQL database named `*_test`."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
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
TEST_IAM_URL = "http://iam.test"

os.environ.update(
    DATABASE_URL=TEST_DATABASE_URL,
    RABBITMQ_URL="amqp://rabbitmq.test",
    JWT_SECRET_KEY=TEST_JWT_SECRET,
    IAM_SERVICE_URL=TEST_IAM_URL,
    CORS_ORIGINS="http://localhost:5173",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.clients.iam import PublicProfile  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


def make_token(user_id: int | str, token_type: str = "access", secret: str = TEST_JWT_SECRET,
               role: str | None = "owner", **overrides) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": str(user_id), "type": token_type, "role": role, "iss": "aparty-iam", "aud": "aparty-api",
              "iat": now, "exp": now + timedelta(minutes=5)}
    claims.update(overrides)
    return jwt.encode(claims, secret, algorithm="HS256")


def auth_headers(user_id: int, role: str | None = "owner") -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id, role=role)}"}


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
        await conn.execute(text("TRUNCATE listing_images, listings CASCADE"))


@pytest_asyncio.fixture
async def db_session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


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
    """Capture RabbitMQ events instead of publishing them."""
    events: list[tuple[str, dict]] = []

    async def fake_publish(routing_key, payload):
        events.append((routing_key, payload))

    monkeypatch.setattr("app.events.publish_event", fake_publish)
    return events


@pytest.fixture(autouse=True)
def iam_profiles(monkeypatch):
    """Owner profiles returned by the fake IAM client; empty means IAM has no data."""
    profiles: dict[int, PublicProfile] = {}

    async def fake_fetch(user_ids):
        return {uid: profiles[uid] for uid in set(user_ids) if uid in profiles}

    monkeypatch.setattr("app.routers.listings.fetch_public_profiles", fake_fetch)
    return profiles


LISTING_PAYLOAD = {
    "title": "Cozy room near campus",
    "price": 1500000,
    "region": "Toshkent shahri",
    "district": "Yunusobod",
    "address": "Amir Temur 1",
    "rooms_count": 2,
    "amenities": {"wifi": True, "kitchen": False},
    "images": ["https://cdn.test/a.jpg"],
}


@pytest_asyncio.fixture
async def create_listing(client):
    async def _create(owner_id: int = 1, role: str = "owner", **overrides):
        response = await client.post(
            "/api/v1/listings", json={**LISTING_PAYLOAD, **overrides}, headers=auth_headers(owner_id, role)
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _create
