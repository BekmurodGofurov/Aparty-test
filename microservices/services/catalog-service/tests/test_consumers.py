import uuid

import pytest

from app.consumers import handle_booking_event, sync_roommate_listing_fullness
from tests.conftest import auth_headers

LISTINGS = "/api/v1/listings"
STUDENT = 20


@pytest.fixture
async def ad(client, create_listing):
    apartment = await create_listing(owner_id=1)
    response = await client.post(
        f"{LISTINGS}/{apartment['id']}/roommate",
        json={"available_spaces": 2, "price": 500000, "residents_male": 1}, headers=auth_headers(STUDENT, "student"),
    )
    assert response.status_code == 201
    return response.json()


def event(listing_id, confirmed, **overrides):
    return {"booking_id": str(uuid.uuid4()), "listing_id": listing_id, "is_roommate_request": True,
            "status": "confirmed", "listing_confirmed_count": confirmed, **overrides}


async def status_of(client, listing_id) -> str:
    return (await client.get(f"{LISTINGS}/{listing_id}/booking-info")).json()["status"]


async def test_ad_becomes_occupied_when_its_places_are_filled(client, ad):
    await handle_booking_event(event(ad["id"], confirmed=1))
    assert await status_of(client, ad["id"]) == "active"

    await handle_booking_event(event(ad["id"], confirmed=2))
    assert await status_of(client, ad["id"]) == "rented"
    found = (await client.get(f"{LISTINGS}/search", params={"owner_role": "student"})).json()
    assert found["total"] == 0


async def test_ad_reopens_when_a_place_frees_up(client, ad):
    await handle_booking_event(event(ad["id"], confirmed=2))
    await handle_booking_event(event(ad["id"], confirmed=1, status="cancelled"))
    assert await status_of(client, ad["id"]) == "active"
    assert (await client.get(f"{LISTINGS}/search", params={"owner_role": "student"})).json()["total"] == 1


async def test_a_manually_closed_ad_is_not_reopened(client, ad):
    await client.post(f"{LISTINGS}/{ad['id']}/mark-occupied", headers=auth_headers(STUDENT, "student"))
    await handle_booking_event(event(ad["id"], confirmed=0, status="cancelled"))
    assert await status_of(client, ad["id"]) == "rented"


async def test_other_events_are_ignored(client, ad, create_listing):
    ordinary = await create_listing(owner_id=5)
    await sync_roommate_listing_fullness(event(ordinary["id"], confirmed=5, is_roommate_request=False))
    await sync_roommate_listing_fullness(event(ordinary["id"], confirmed=5))  # a listing that is not a roommate ad
    await sync_roommate_listing_fullness(event(str(uuid.uuid4()), confirmed=5))
    await sync_roommate_listing_fullness({"status": "confirmed"})
    assert await status_of(client, ordinary["id"]) == "active"
    assert await status_of(client, ad["id"]) == "active"


async def test_closed_ads_stay_closed(client, ad):
    await client.delete(f"{LISTINGS}/{ad['id']}", headers=auth_headers(STUDENT, "student"))
    await handle_booking_event(event(ad["id"], confirmed=0))
    assert (await client.get(f"{LISTINGS}/{ad['id']}/booking-info")).status_code == 404
