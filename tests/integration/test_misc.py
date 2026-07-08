"""Integration tests for subscriptions, favorites, notifications, health."""

import pytest
from httpx import AsyncClient

from app.models.listing import Listing
from app.models.user import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_get_my_subscriptions(client: AsyncClient, makler_user: User):
    response = await client.get("/api/v1/subscriptions/me", headers=auth_headers(makler_user))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_purchase_subscription_plan(client: AsyncClient, makler_user: User):
    response = await client.post("/api/v1/subscriptions/s", headers=auth_headers(makler_user))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_purchase_unknown_plan(client: AsyncClient, makler_user: User):
    response = await client.post("/api/v1/subscriptions/unknown", headers=auth_headers(makler_user))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_toggle_favorite_add(client: AsyncClient, student_user: User, active_listing: Listing):
    response = await client.post(
        f"/api/v1/favorites/{active_listing.id}",
        headers=auth_headers(student_user),
    )
    assert response.status_code == 201
    assert response.json()["status"] == "added"


@pytest.mark.asyncio
async def test_get_my_favorites(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/favorites/me", headers=auth_headers(student_user))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_notifications(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/notifications/me", headers=auth_headers(student_user))
    assert response.status_code == 200
    assert "unread_count" in response.json()


@pytest.mark.asyncio
async def test_mark_all_notifications_read(client: AsyncClient, student_user: User):
    response = await client.patch("/api/v1/notifications/read-all", headers=auth_headers(student_user))
    assert response.status_code == 200
