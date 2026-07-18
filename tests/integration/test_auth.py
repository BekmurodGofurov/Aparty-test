"""Integration tests for auth API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.user import User, UserRole
from app.utils.login_code_store import generate_login_code
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "id": 999111222,
            "full_name": "Auth Test",
            "phone": "+998908887766",
            "role": "student",
        },
    )
    assert response.status_code == 201
    assert response.json()["phone"] == "+998908887766"


@pytest.mark.asyncio
async def test_register_duplicate_phone(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "id": 999111223,
            "full_name": "Duplicate",
            "phone": student_user.phone,
            "role": "student",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_admin_forbidden(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "id": 999111224,
            "full_name": "Bad Admin",
            "phone": "+998908887767",
            "role": "admin",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_validation_error(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"full_name": "X", "phone": "bad", "role": "student"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, student_user: User):
    code = generate_login_code(str(student_user.id))
    response = await client.post(
        "/api/v1/auth/login",
        json={"code": code},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_login_invalid_code(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"code": "000000"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_bot_login_code_success(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/auth/bot/login-code",
        json={"id": student_user.id},
    )
    assert response.status_code == 200
    assert len(response.json()["code"]) == 6


@pytest.mark.asyncio
async def test_refresh_missing_token(client: AsyncClient):
    response = await client.post("/api/v1/auth/refresh", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/auth/me", headers=auth_headers(student_user))
    assert response.status_code == 200
    assert response.json()["id"] == student_user.id


@pytest.mark.asyncio
async def test_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_bot_check_existing(client: AsyncClient, student_user: User):
    response = await client.get(f"/api/v1/auth/bot/check/{student_user.id}")
    assert response.status_code == 200
    assert response.json()["data"]["exists"] is True
    response = await client.get(f"/api/v1/auth/bot/check/phone/{student_user.phone}")
    assert response.status_code == 200
    assert response.json()["data"]["exists"] is True


@pytest.mark.asyncio
async def test_bot_check_missing(client: AsyncClient):
    response = await client.get("/api/v1/auth/bot/check/phone/+998900000098")
    assert response.status_code == 200
    assert response.json()["data"]["exists"] is False
