"""E2E Scenario 1: Guest registers -> verifies OTP -> searches listing -> books rental."""

import pytest
from httpx import AsyncClient

from app.utils.security import DEV_OTP_CODE
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_guest_journey_register_verify_search_book(
    client: AsyncClient,
    active_listing,
):
    phone = "+998909998877"
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Guest Journey",
            "phone": phone,
            "password": "password123",
            "role": "student",
        },
    )
    assert register_response.status_code == 201

    otp_response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": DEV_OTP_CODE},
    )
    assert otp_response.status_code == 200
    token = otp_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    search_response = await client.get(
        "/api/v1/listings/search",
        params={"region": active_listing.region},
    )
    assert search_response.status_code == 200
    assert search_response.json()["total"] >= 1

    book_response = await client.post(
        "/api/v1/rentals/requests",
        json={"listing_id": str(active_listing.id), "message": "Please accept my request"},
        headers=headers,
    )
    assert book_response.status_code == 200
    assert book_response.json()["status"] == "pending"

    my_requests = await client.get("/api/v1/rentals/requests/me", headers=headers)
    assert my_requests.status_code == 200
    assert len(my_requests.json()) >= 1
