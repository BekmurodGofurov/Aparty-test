"""Shared fixtures. Tests run against a real PostgreSQL database named `*_test`."""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
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
TEST_BOT_TOKEN = "123456:TEST-BOT-TOKEN"
TEST_SITE_URL = "https://aparty.test"

os.environ.update(
    DATABASE_URL=TEST_DATABASE_URL,
    RABBITMQ_URL="amqp://rabbitmq.test",
    JWT_SECRET_KEY=TEST_JWT_SECRET,
    IAM_SERVICE_URL="http://iam.test",
    BOT_TOKEN=TEST_BOT_TOKEN,
    SITE_URL=TEST_SITE_URL,
    CORS_ORIGINS="http://localhost:5173",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Notification  # noqa: E402
from app.schemas import PublicProfile  # noqa: E402
from tests.helpers import mock_outbound_http  # noqa: E402


def make_token(user_id: int | str, token_type: str = "access", secret: str = TEST_JWT_SECRET, **overrides) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": str(user_id), "type": token_type, "role": "student", "iss": "aparty-iam", "aud": "aparty-api",
              "iat": now, "exp": now + timedelta(minutes=5)}
    claims.update(overrides)
    return jwt.encode(claims, secret, algorithm="HS256")


def auth_headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id)}"}


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
        await conn.execute(text("TRUNCATE notifications"))


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


@pytest_asyncio.fixture
async def db(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


class FakeTelegram:
    """Stands in for the Telegram Bot API and records what was sent."""

    def __init__(self):
        self.calls: list[dict] = []
        self.urls: list[str] = []
        self.status_code = 200
        self.response: dict = {"ok": True, "result": {}}
        self.raise_network_error = False

    def handle(self, request: httpx.Request) -> httpx.Response:
        if self.raise_network_error:
            raise httpx.ConnectError("telegram unreachable")
        self.urls.append(str(request.url))
        self.calls.append(json.loads(request.content))
        return httpx.Response(self.status_code, json=self.response)


@pytest.fixture(autouse=True)
def telegram(monkeypatch):
    fake = FakeTelegram()
    mock_outbound_http(monkeypatch, fake.handle)
    return fake


@pytest.fixture(autouse=True)
def iam_profiles(monkeypatch):
    """Requester profiles returned by the fake IAM client; empty means IAM has no data."""
    profiles: dict[int, PublicProfile] = {}

    async def fake_fetch(user_ids):
        return {uid: profiles[uid] for uid in set(user_ids) if uid in profiles}

    monkeypatch.setattr("app.handlers.fetch_public_profiles", fake_fetch)
    return profiles


@pytest_asyncio.fixture
async def add_notification(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _add(user_id: int, title: str = "Hello", is_read: bool = False, minutes_ago: int = 0, **fields):
        async with factory() as session:
            item = Notification(
                user_id=user_id, type="test", title=title, body=fields.get("body"), is_read=is_read,
                target_url=fields.get("target_url"), dedupe_key=str(uuid.uuid4()),
                created_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
            )
            session.add(item)
            await session.commit()
            return item

    return _add


async def stored_notifications(engine, user_id: int | None = None) -> list[Notification]:
    from sqlalchemy import select

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        stmt = select(Notification).order_by(Notification.created_at)
        if user_id is not None:
            stmt = stmt.where(Notification.user_id == user_id)
        return list((await session.execute(stmt)).scalars().all())
