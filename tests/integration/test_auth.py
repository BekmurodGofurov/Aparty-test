"""Integration tests for auth API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.user import User, UserRole
from app.utils.security import DEV_OTP_CODE, hash_password
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Auth Test",
            "phone": "+998908887766",
            "password": "password123",
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
            "full_name": "Duplicate",
            "phone": student_user.phone,
            "password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_admin_forbidden(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Bad Admin",
            "phone": "+998908887767",
            "password": "password123",
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
    response = await client.post(
        "/api/v1/auth/login",
        json={"phone": student_user.phone, "password": "password123"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"phone": student_user.phone, "password": "wrong"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_admin_login_forbidden_for_student(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/auth/admin-login",
        json={"phone": student_user.phone, "password": "password123"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_login_success(client: AsyncClient, admin_user: User):
    response = await client.post(
        "/api/v1/auth/admin-login",
        json={"phone": admin_user.phone, "password": "password123"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_otp_verify_success(client: AsyncClient, db_session):
    phone = "+998909991122"
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "OTP User", "phone": phone, "password": "password123", "role": "student"},
    )
    response = await client.post("/api/v1/auth/otp/verify", json={"phone": phone, "otp": DEV_OTP_CODE})
    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_otp_verify_invalid_code(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": student_user.phone, "otp": "999999"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_otp_verify_user_not_found(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": "+998900000099", "otp": DEV_OTP_CODE},
    )
    assert response.status_code == 404


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
    assert response.json()["id"] == str(student_user.id)


@pytest.mark.asyncio
async def test_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_bot_check_existing(client: AsyncClient, student_user: User):
    response = await client.get(f"/api/v1/auth/bot/check/{student_user.phone}")
    assert response.status_code == 200
    assert response.json()["data"]["exists"] is True


@pytest.mark.asyncio
async def test_bot_check_missing(client: AsyncClient):
    response = await client.get("/api/v1/auth/bot/check/+998900000098")
    assert response.status_code == 200
    assert response.json()["data"]["exists"] is False
