"""Integration tests for reviews API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.listing import Listing
from app.models.user import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_review(client: AsyncClient, student_user: User, active_listing: Listing):
    response = await client.post(
        "/api/v1/reviews/",
        json={"listing_id": str(active_listing.id), "rating": 5, "review_text": "Great place"},
        headers=auth_headers(student_user),
    )
    assert response.status_code == 200
    assert response.json()["rating"] == 5


@pytest.mark.asyncio
async def test_create_duplicate_review_forbidden(
    client: AsyncClient,
    student_user: User,
    active_listing: Listing,
):
    payload = {"listing_id": str(active_listing.id), "rating": 4, "review_text": "Nice"}
    await client.post("/api/v1/reviews/", json=payload, headers=auth_headers(student_user))
    response = await client.post("/api/v1/reviews/", json=payload, headers=auth_headers(student_user))
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_review_listing_not_found(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/reviews/",
        json={
            "listing_id": "00000000-0000-0000-0000-000000000099",
            "rating": 3,
            "review_text": "Missing",
        },
        headers=auth_headers(student_user),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_reviews_by_listing(client: AsyncClient, active_listing: Listing):
    response = await client.get(f"/api/v1/reviews/listing/{active_listing.id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
