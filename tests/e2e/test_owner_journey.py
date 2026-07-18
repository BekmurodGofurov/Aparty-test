"""E2E Scenario 2: Owner registers -> creates premium listing -> accepts rental -> receives payment."""

from datetime import date

import pytest
from httpx import AsyncClient

from app.utils.login_code_store import generate_login_code
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_owner_journey_premium_listing_accept_payment(client: AsyncClient, student_user):
    owner_id = 999888777
    phone = "+998908776655"
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "id": owner_id,
            "full_name": "Owner Journey",
            "phone": phone,
            "role": "owner",
        },
    )
    assert register_response.status_code == 201
    assert register_response.json()["id"] == owner_id

    code = generate_login_code(str(owner_id))
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"code": code},
    )
    owner_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    listing_payload = {
        "region": "Samarqand",
        "district": "Registon",
        "address": "Owner Premium St 1",
        "latitude": 39.6542,
        "longitude": 66.9597,
        "rooms_count": 3,
        "area_m2": 70,
        "price_usd": 350,
        "target_gender": "mixed",
        "max_guests": 3,
        "available_spaces": 2,
        "amenities": {"wifi": True, "gas": True, "water": True},
        "images": ["https://example.com/premium.jpg"],
        "description": "Premium owner listing",
        "is_premium": True,
    }
    create_response = await client.post("/api/v1/listings/", json=listing_payload, headers=owner_headers)
    assert create_response.status_code == 201
    listing = create_response.json()
    assert listing["owner_id"] == owner_id
    assert listing["is_premium"] is True

    await client.post(
        f"/api/v1/listings/{listing['id']}/activate-basic",
        headers=owner_headers,
    )

    student_headers = auth_headers(student_user)
    request_response = await client.post(
        "/api/v1/rentals/requests",
        json={"listing_id": listing["id"], "message": "Need a room"},
        headers=student_headers,
    )
    assert request_response.status_code == 200
    request_id = request_response.json()["id"]

    accept_response = await client.patch(
        f"/api/v1/rentals/requests/{request_id}/accept",
        headers=owner_headers,
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "accepted"
    rental_id = accept_response.json()["rental_id"]

    payment_response = await client.post(
        "/api/v1/payments/",
        json={
            "rental_id": rental_id,
            "payer_id": student_user.id,
            "amount": 350,
            "billing_month": str(date.today().replace(day=1)),
        },
        headers=student_headers,
    )
    assert payment_response.status_code == 200
    assert payment_response.json()["amount"] == 350
