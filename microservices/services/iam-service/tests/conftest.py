"""Shared fixtures. Tests run against a real PostgreSQL database named `*_test`."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from fakeredis import FakeAsyncRedis, FakeServer
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")
if not TEST_DATABASE_URL.rsplit("/", 1)[-1].endswith("_test"):
    sys.exit("Set TEST_DATABASE_URL to a PostgreSQL database whose name ends with '_test'.")

TEST_JWT_SECRET = "test-only-jwt-secret-with-at-least-32-bytes"
TEST_ADMIN_USERNAME = "test-admin"
TEST_ADMIN_PASSWORD = "test-admin-password"
TELEGRAM_CLIENT_ID = "123456"
TELEGRAM_CLIENT_SECRET = "test-client-secret"
TELEGRAM_REDIRECT_URI = "http://localhost:5173/auth/telegram/callback"
AUTH_CODE = "telegram-auth-code"

os.environ.update(
    DATABASE_URL=TEST_DATABASE_URL,
    REDIS_URL="redis://redis.test:6379",
    JWT_SECRET_KEY=TEST_JWT_SECRET,
    ADMIN_USERNAME=TEST_ADMIN_USERNAME,
    ADMIN_PASSWORD=TEST_ADMIN_PASSWORD,
    CORS_ORIGINS="http://localhost:5173",
    TELEGRAM_CLIENT_ID=TELEGRAM_CLIENT_ID,
    TELEGRAM_CLIENT_SECRET=TELEGRAM_CLIENT_SECRET,
    TELEGRAM_REDIRECT_URI=TELEGRAM_REDIRECT_URI,
    LOGIN_RATE_LIMIT_PER_MINUTE="100",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.redis_client as redis_client  # noqa: E402
import app.telegram_oidc as telegram_oidc  # noqa: E402
from app.config import settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.security import create_access_token  # noqa: E402
from tests.helpers import mock_outbound_http  # noqa: E402


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
        await conn.execute(text("TRUNCATE users CASCADE"))


@pytest_asyncio.fixture
async def client(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as http_client:
        yield http_client
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def fake_redis(monkeypatch):
    redis = FakeAsyncRedis(server=FakeServer(), decode_responses=True)
    monkeypatch.setattr(redis_client, "_redis", redis)
    yield redis
    await redis.aclose()


@pytest.fixture(autouse=True)
def reset_jwks_cache():
    telegram_oidc._jwks_cache.update(keys={}, fetched_at=0.0)


class FakeTelegram:
    """Stands in for oauth.telegram.org: token endpoint and signing keys."""

    kid = "test-key-1"

    def __init__(self):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.challenge: str | None = None
        self.overrides: dict = {}
        self.token_endpoint_status = 200
        self.jwks_requests = 0

    def jwks(self) -> dict:
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.private_key.public_key()))
        return {"keys": [{**jwk, "kid": self.kid, "alg": "RS256", "use": "sig"}]}

    def id_token(self, key=None, kid: str | None = None, **overrides) -> str:
        now = int(time.time())
        claims = {
            "iss": settings.telegram_issuer,
            "aud": TELEGRAM_CLIENT_ID,
            "sub": "555001",
            "id": 555001,
            "iat": now,
            "exp": now + 300,
            "name": "Aziz Karimov",
            "preferred_username": "aziz",
            "picture": "https://t.me/i/userpic/aziz.jpg",
            "phone_number": "998901234567",
            "phone_number_verified": True,
        }
        claims.update(self.overrides)
        claims.update(overrides)
        claims = {k: v for k, v in claims.items() if v is not None}
        return jwt.encode(claims, key or self.private_key, algorithm="RS256", headers={"kid": kid or self.kid})

    def handle(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("jwks.json"):
            self.jwks_requests += 1
            return httpx.Response(200, json=self.jwks())

        expected_auth = "Basic " + base64.b64encode(f"{TELEGRAM_CLIENT_ID}:{TELEGRAM_CLIENT_SECRET}".encode()).decode()
        form = dict(pair.split("=", 1) for pair in request.content.decode().split("&"))
        verifier_digest = hashlib.sha256(form["code_verifier"].encode()).digest()
        challenge = base64.urlsafe_b64encode(verifier_digest).rstrip(b"=").decode()
        valid = (
            request.headers.get("authorization") == expected_auth
            and form["code"] == AUTH_CODE
            and challenge == self.challenge
        )
        if self.token_endpoint_status != 200 or not valid:
            return httpx.Response(400 if valid else 401, json={"error": "invalid_grant"})
        return httpx.Response(200, json={"id_token": self.id_token(), "token_type": "Bearer"})


@pytest.fixture
def telegram(monkeypatch):
    fake = FakeTelegram()
    mock_outbound_http(monkeypatch, fake.handle)
    return fake


async def start_login(client, telegram: FakeTelegram) -> str:
    """Call /auth/telegram/start, remember the PKCE challenge and return the state."""
    response = await client.get("/api/v1/auth/telegram/start")
    assert response.status_code == 200, response.text
    query = parse_qs(urlsplit(response.json()["authorization_url"]).query)
    telegram.challenge = query["code_challenge"][0]
    return query["state"][0]


async def login_with_telegram(client, telegram: FakeTelegram):
    state = await start_login(client, telegram)
    return await client.post("/api/v1/auth/telegram/callback", json={"code": AUTH_CODE, "state": state})


@pytest_asyncio.fixture
async def create_user(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _create(user_id: int = 1, role: UserRole | None = UserRole.owner, **overrides) -> User:
        fields = {
            "id": user_id,
            "full_name": f"User {user_id}",
            "phone": f"+99890000{user_id:04d}",
            "role": role,
            "is_verified": True,
        }
        async with factory() as session:
            user = User(**{**fields, **overrides})
            session.add(user)
            await session.commit()
            return user

    return _create


def auth_headers(user_id: int | str, role: str | None = "owner") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, role)}"}
