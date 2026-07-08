"""End-to-end test simulating a full user journey."""

import pytest
from httpx import AsyncClient

from app.utils.security import DEV_OTP_CODE


@pytest.mark.asyncio
async def test_user_journey_register_verify_create_and_search(client: AsyncClient):
    phone = "+998909998877"
    register_payload = {
        "full_name": "Journey User",
        "phone": phone,
        "password": "password123",
        "role": "makler",
    }

    register_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]

    otp_response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": DEV_OTP_CODE},
    )
    assert otp_response.status_code == 200
    token_data = otp_response.json()
    assert token_data["access_token"]
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    listing_payload = {
        "region": "Andijon",
        "district": "Andijon shahri",
        "address": "Journey Street 42",
        "latitude": 40.7821,
        "longitude": 72.3442,
        "rooms_count": 2,
        "area_m2": 48,
        "price_usd": 180,
        "target_gender": "mixed",
        "max_guests": 2,
        "available_spaces": 1,
        "amenities": {"wifi": True, "gas": True, "water": True},
        "images": ["https://example.com/journey.jpg"],
        "description": "E2E journey listing",
        "is_premium": False,
    }

    create_response = await client.post("/api/v1/listings/", json=listing_payload, headers=headers)
    assert create_response.status_code == 201
    created_listing = create_response.json()
    assert created_listing["owner_id"] == user_id
    assert created_listing["is_active"] is True

    search_response = await client.get(
        "/api/v1/listings/search",
        params={"region": "Andijon", "district": "Andijon shahri"},
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert search_data["total"] >= 1
    found_ids = [item["id"] for item in search_data["listings"]]
    assert created_listing["id"] in found_ids

    detail_response = await client.get(f"/api/v1/listings/{created_listing['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["description"] == "E2E journey listing"
