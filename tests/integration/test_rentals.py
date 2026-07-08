"""Integration tests for rentals API endpoints."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient

from app.models.listing import Listing
from app.models.user import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_rental_request(
    client: AsyncClient,
    student_user: User,
    active_listing: Listing,
):
    response = await client.post(
        "/api/v1/rentals/requests",
        json={"listing_id": str(active_listing.id), "message": "I want this room"},
        headers=auth_headers(student_user),
    )
    assert response.status_code == 200
    assert response.json()["listing_id"] == str(active_listing.id)


@pytest.mark.asyncio
async def test_create_rental_request_own_listing_forbidden(
    client: AsyncClient,
    makler_user: User,
    active_listing: Listing,
):
    response = await client.post(
        "/api/v1/rentals/requests",
        json={"listing_id": str(active_listing.id)},
        headers=auth_headers(makler_user),
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_rental_request_listing_not_found(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/rentals/requests",
        json={"listing_id": str(uuid.uuid4())},
        headers=auth_headers(student_user),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_rental_requests(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/rentals/requests/me", headers=auth_headers(student_user))
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_rental_conversations(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/rentals/conversations", headers=auth_headers(student_user))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_owner_rentals_forbidden_for_student(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/rentals/owner/me", headers=auth_headers(student_user))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_my_rooms(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/rentals/me/rooms", headers=auth_headers(student_user))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_rental_direct(
    client: AsyncClient,
    student_user: User,
    active_listing: Listing,
):
    response = await client.post(
        "/api/v1/rentals/",
        json={
            "listing_id": str(active_listing.id),
            "student_id": str(student_user.id),
            "start_date": str(date.today()),
            "price_usd": 200,
        },
        headers=auth_headers(student_user),
    )
    assert response.status_code == 200
