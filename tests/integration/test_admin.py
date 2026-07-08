"""Integration tests for admin API endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.listing import Listing
from app.models.user import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_dashboard_requires_admin(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/admin/dashboard", headers=auth_headers(student_user))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_success(client: AsyncClient, admin_user: User):
    response = await client.get("/api/v1/admin/dashboard", headers=auth_headers(admin_user))
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "listings" in data


@pytest.mark.asyncio
async def test_all_users(client: AsyncClient, admin_user: User):
    response = await client.get("/api/v1/admin/users", headers=auth_headers(admin_user))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_user_detail_not_found(client: AsyncClient, admin_user: User):
    response = await client.get(
        f"/api/v1/admin/users/{uuid.uuid4()}/detail",
        headers=auth_headers(admin_user),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_set_user_status(client: AsyncClient, admin_user: User, student_user: User):
    response = await client.patch(
        f"/api/v1/admin/users/{student_user.id}/status",
        json={"is_verified": True},
        headers=auth_headers(admin_user),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_all_listings(client: AsyncClient, admin_user: User):
    response = await client.get("/api/v1/admin/listings", headers=auth_headers(admin_user))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_listing_detail(client: AsyncClient, admin_user: User, active_listing: Listing):
    response = await client.get(
        f"/api/v1/admin/listings/{active_listing.id}/detail",
        headers=auth_headers(admin_user),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_set_listing_status(client: AsyncClient, admin_user: User, active_listing: Listing):
    response = await client.patch(
        f"/api/v1/admin/listings/{active_listing.id}/status",
        json={"is_active": False},
        headers=auth_headers(admin_user),
    )
    assert response.status_code == 200
