"""Integration tests for users API endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/users/me", headers=auth_headers(student_user))
    assert response.status_code == 200
    assert response.json()["phone"] == student_user.phone


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, student_user: User):
    response = await client.get(f"/api/v1/users/{student_user.id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    response = await client.get(f"/api/v1/users/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_current_user(client: AsyncClient, student_user: User):
    response = await client.put(
        "/api/v1/users/me",
        json={"full_name": "Updated Name"},
        headers=auth_headers(student_user),
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_current_user(client: AsyncClient, db_session):
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    user = User(
        full_name="Delete Me",
        phone="+998903333333",
        role=UserRole.student,
        hashed_password=hash_password("password123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.delete("/api/v1/users/me", headers=auth_headers(user))
    assert response.status_code == 204
