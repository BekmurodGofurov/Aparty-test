"""Integration tests for listing API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.listing import Listing
from app.models.user import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_listing_success(
    client: AsyncClient,
    makler_user: User,
    sample_listing_payload: dict,
):
    response = await client.post(
        "/api/v1/listings/",
        json=sample_listing_payload,
        headers=auth_headers(makler_user),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["region"] == sample_listing_payload["region"]
    assert data["owner_id"] == makler_user.id


@pytest.mark.asyncio
async def test_create_listing_forbidden_for_student(
    client: AsyncClient,
    student_user: User,
    sample_listing_payload: dict,
):
    response = await client.post(
        "/api/v1/listings/",
        json=sample_listing_payload,
        headers=auth_headers(student_user),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_listing_validation_error(client: AsyncClient, makler_user: User):
    response = await client.post(
        "/api/v1/listings/",
        json={"region": "X"},
        headers=auth_headers(makler_user),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_listings_returns_cards(client: AsyncClient, active_listing: Listing):
    response = await client.get(
        "/api/v1/listings/search",
        params={"region": active_listing.region, "district": active_listing.district},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_listing_detail(client: AsyncClient, active_listing: Listing):
    response = await client.get(f"/api/v1/listings/{active_listing.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(active_listing.id)


@pytest.mark.asyncio
async def test_get_listing_not_found(client: AsyncClient):
    response = await client.get("/api/v1/listings/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_listings(client: AsyncClient, makler_user: User, active_listing: Listing):
    response = await client.get("/api/v1/listings/me", headers=auth_headers(makler_user))
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_listing_forbidden(client: AsyncClient, student_user: User, active_listing: Listing):
    response = await client.patch(
        f"/api/v1/listings/{active_listing.id}",
        json={"description": "Hacked"},
        headers=auth_headers(student_user),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_listing_not_found(client: AsyncClient, makler_user: User):
    response = await client.delete(
        "/api/v1/listings/00000000-0000-0000-0000-000000000099",
        headers=auth_headers(makler_user),
    )
    assert response.status_code == 404
