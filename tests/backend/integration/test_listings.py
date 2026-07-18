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
    db_session,
):
    response = await client.post(
        "/api/v1/listings/",
        json=sample_listing_payload,
        headers=auth_headers(makler_user),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["region"] == sample_listing_payload["region"]
    assert data["district"] == sample_listing_payload["district"]
    assert data["price_usd"] == sample_listing_payload["price_usd"]
    assert data["owner_id"] == makler_user.id
    assert data["source"] == "makler"


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
    assert response.json()["detail"] == "Insufficient permissions"


@pytest.mark.asyncio
async def test_search_listings_returns_cards(
    client: AsyncClient,
    active_listing: Listing,
):
    response = await client.get(
        "/api/v1/listings/search",
        params={"region": active_listing.region, "district": active_listing.district},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] >= 1
    listing_ids = [item["id"] for item in data["listings"]]
    assert str(active_listing.id) in listing_ids


@pytest.mark.asyncio
async def test_get_listing_detail(
    client: AsyncClient,
    active_listing: Listing,
):
    response = await client.get(f"/api/v1/listings/{active_listing.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(active_listing.id)
    assert data["region"] == active_listing.region
    assert data["price_usd"] == active_listing.price_usd
