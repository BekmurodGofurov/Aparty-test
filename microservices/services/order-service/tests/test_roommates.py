import asyncio

import pytest

from tests.conftest import GUEST_ID, OWNER_ID, auth_headers, in_days

BASE = "/api/v1/bookings"
TENANT = GUEST_ID  # the student who rents the apartment and looks for roommates
CO_TENANT = 30
NEWCOMER = 40


@pytest.fixture
async def apartment(client, catalog, create_booking):
    """An apartment rented by TENANT (confirmed) with a roommate listing offering two places."""
    apartment_id = catalog.add(owner_id=OWNER_ID)
    tenancy = await create_booking(apartment_id, guest_id=TENANT, start=1, end=60)
    confirmed = await client.patch(f"{BASE}/{tenancy['id']}/status", json={"status": "confirmed"},
                                   headers=auth_headers(OWNER_ID))
    assert confirmed.status_code == 200
    roommate_listing = catalog.add(
        owner_id=TENANT, parent_listing_id=apartment_id, rental_type="shared_room", available_spaces=2
    )
    return {"apartment": apartment_id, "roommate_listing": roommate_listing, "tenancy": tenancy}


async def request_spot(client, listing_id, user_id=NEWCOMER, start=5, end=10):
    return await client.post(
        BASE, json={"listing_id": str(listing_id), "start_date": in_days(start), "end_date": in_days(end)},
        headers=auth_headers(user_id),
    )


async def add_resident(client, catalog, create_booking, apartment_id, user_id=CO_TENANT):
    """A second confirmed tenant of the same apartment, with dates that do not clash with TENANT's."""
    booking = await create_booking(apartment_id, guest_id=user_id, start=61, end=90)
    await client.patch(f"{BASE}/{booking['id']}/status", json={"status": "confirmed"}, headers=auth_headers(OWNER_ID))
    return booking


async def test_roommate_request_is_linked_to_the_apartment(client, apartment, published_events):
    response = await request_spot(client, apartment["roommate_listing"])
    assert response.status_code == 201
    body = response.json()
    assert body["is_roommate_request"] is True
    assert body["apartment_listing_id"] == str(apartment["apartment"])
    assert body["listing_id"] == str(apartment["roommate_listing"])
    assert body["listing_owner_id"] == TENANT
    assert published_events[-1][1]["is_roommate_request"] is True


async def test_normal_booking_is_not_a_roommate_request(create_booking, catalog):
    booking = await create_booking(catalog.add())
    assert booking["is_roommate_request"] is False
    assert booking["apartment_listing_id"] == booking["listing_id"]


async def test_the_listing_creator_sees_and_answers_the_request(client, apartment):
    request = (await request_spot(client, apartment["roommate_listing"])).json()
    incoming = await client.get(f"{BASE}/incoming", headers=auth_headers(TENANT))
    assert [item["id"] for item in incoming.json()] == [request["id"]]

    confirmed = await client.patch(f"{BASE}/{request['id']}/status", json={"status": "confirmed"},
                                   headers=auth_headers(TENANT))
    assert confirmed.json()["status"] == "confirmed"


async def test_any_resident_of_the_apartment_can_accept(client, catalog, create_booking, apartment):
    await add_resident(client, catalog, create_booking, apartment["apartment"])
    request = (await request_spot(client, apartment["roommate_listing"])).json()

    seen = await client.get(f"{BASE}/incoming", headers=auth_headers(CO_TENANT))
    assert [item["id"] for item in seen.json()] == [request["id"]]
    assert (await client.get(f"{BASE}/{request['id']}", headers=auth_headers(CO_TENANT))).status_code == 200

    accepted = await client.patch(f"{BASE}/{request['id']}/status", json={"status": "confirmed"},
                                  headers=auth_headers(CO_TENANT))
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "confirmed"


async def test_any_resident_can_decline(client, catalog, create_booking, apartment):
    await add_resident(client, catalog, create_booking, apartment["apartment"])
    request = (await request_spot(client, apartment["roommate_listing"])).json()
    declined = await client.patch(f"{BASE}/{request['id']}/status", json={"status": "rejected"},
                                  headers=auth_headers(CO_TENANT))
    assert declined.json()["status"] == "rejected"


async def test_co_tenant_cannot_cancel_an_accepted_roommate(client, catalog, create_booking, apartment):
    await add_resident(client, catalog, create_booking, apartment["apartment"])
    request = (await request_spot(client, apartment["roommate_listing"])).json()
    url = f"{BASE}/{request['id']}/status"
    await client.patch(url, json={"status": "confirmed"}, headers=auth_headers(TENANT))
    response = await client.patch(url, json={"status": "cancelled"}, headers=auth_headers(CO_TENANT))
    assert response.status_code == 409


async def test_accepted_roommates_become_residents_who_can_answer_next_requests(client, apartment):
    first = (await request_spot(client, apartment["roommate_listing"], NEWCOMER)).json()
    await client.patch(f"{BASE}/{first['id']}/status", json={"status": "confirmed"}, headers=auth_headers(TENANT))

    second = (await request_spot(client, apartment["roommate_listing"], 50)).json()
    seen = await client.get(f"{BASE}/incoming", headers=auth_headers(NEWCOMER))
    assert [item["id"] for item in seen.json()] == [second["id"]]
    accepted = await client.patch(f"{BASE}/{second['id']}/status", json={"status": "confirmed"},
                                  headers=auth_headers(NEWCOMER))
    assert accepted.status_code == 200


async def test_strangers_and_other_apartments_have_no_access(client, catalog, create_booking, apartment):
    request = (await request_spot(client, apartment["roommate_listing"])).json()
    other_apartment = catalog.add(owner_id=OWNER_ID)
    other = await create_booking(other_apartment, guest_id=60, start=1, end=60)
    await client.patch(f"{BASE}/{other['id']}/status", json={"status": "confirmed"}, headers=auth_headers(OWNER_ID))

    for user_id in (77, 60):
        assert (await client.get(f"{BASE}/{request['id']}", headers=auth_headers(user_id))).status_code == 403
        patch = await client.patch(f"{BASE}/{request['id']}/status", json={"status": "confirmed"},
                                   headers=auth_headers(user_id))
        assert patch.status_code == 403
        assert (await client.get(f"{BASE}/incoming", headers=auth_headers(user_id))).json() == []


async def test_a_pending_tenant_cannot_answer_requests(client, catalog, create_booking, apartment):
    pending = await create_booking(apartment["apartment"], guest_id=CO_TENANT, start=61, end=90)
    request = (await request_spot(client, apartment["roommate_listing"])).json()
    response = await client.patch(f"{BASE}/{request['id']}/status", json={"status": "confirmed"},
                                  headers=auth_headers(CO_TENANT))
    assert pending["status"] == "pending"
    assert response.status_code == 403


async def test_an_expired_tenancy_no_longer_grants_access(client, engine, apartment):
    from sqlalchemy import text

    request = (await request_spot(client, apartment["roommate_listing"])).json()
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE bookings SET end_date = CURRENT_DATE - 1 WHERE user_id = :u AND NOT is_roommate_request"),
                           {"u": TENANT})
    seen = await client.get(f"{BASE}/incoming", headers=auth_headers(TENANT))
    assert [item["id"] for item in seen.json()] == [request["id"]]  # the creator still owns the listing
    other = await client.get(f"{BASE}/incoming", headers=auth_headers(CO_TENANT))
    assert other.json() == []


async def test_a_resident_cannot_request_a_spot_in_their_own_apartment(client, catalog, create_booking, apartment):
    await add_resident(client, catalog, create_booking, apartment["apartment"])
    response = await request_spot(client, apartment["roommate_listing"], user_id=CO_TENANT)
    assert response.status_code == 400


async def test_spots_are_limited_by_the_offered_places(client, apartment):
    listing = apartment["roommate_listing"]
    assert (await request_spot(client, listing, 41)).status_code == 201
    assert (await request_spot(client, listing, 42)).status_code == 201
    assert (await request_spot(client, listing, 43)).status_code == 409
    assert (await request_spot(client, listing, 43, start=10, end=15)).status_code == 201  # different dates


async def test_a_person_cannot_hold_two_spots_for_the_same_dates(client, apartment):
    listing = apartment["roommate_listing"]
    assert (await request_spot(client, listing, 41)).status_code == 201
    assert (await request_spot(client, listing, 41, start=6, end=8)).status_code == 409


async def test_declined_requests_free_a_spot(client, apartment):
    listing = apartment["roommate_listing"]
    first = (await request_spot(client, listing, 41)).json()
    await request_spot(client, listing, 42)
    await client.patch(f"{BASE}/{first['id']}/status", json={"status": "rejected"}, headers=auth_headers(TENANT))
    assert (await request_spot(client, listing, 43)).status_code == 201


async def test_concurrent_requests_respect_the_capacity(client, apartment):
    listing = apartment["roommate_listing"]
    responses = await asyncio.gather(*(request_spot(client, listing, user) for user in (41, 42, 43, 44)))
    assert sorted(r.status_code for r in responses) == [201, 201, 409, 409]


async def test_a_listing_with_no_offered_places_is_full(client, catalog):
    parent = catalog.add(owner_id=OWNER_ID)
    listing = catalog.add(owner_id=TENANT, parent_listing_id=parent, rental_type="shared_room", available_spaces=0)
    assert (await request_spot(client, listing)).status_code == 409


async def test_shared_rooms_from_owners_also_use_offered_places(client, catalog):
    listing = catalog.add(owner_id=OWNER_ID, rental_type="shared_room", available_spaces=2)
    assert (await request_spot(client, listing, 41)).status_code == 201
    assert (await request_spot(client, listing, 42)).status_code == 201
    assert (await request_spot(client, listing, 43)).status_code == 409


async def test_events_report_how_many_places_are_confirmed(client, apartment, published_events):
    listing = apartment["roommate_listing"]
    first = (await request_spot(client, listing, 41)).json()
    second = (await request_spot(client, listing, 42)).json()
    assert published_events[-1][1]["listing_confirmed_count"] == 0

    await client.patch(f"{BASE}/{first['id']}/status", json={"status": "confirmed"}, headers=auth_headers(TENANT))
    assert published_events[-1][0] == "booking.updated"
    assert published_events[-1][1]["listing_confirmed_count"] == 1

    await client.patch(f"{BASE}/{second['id']}/status", json={"status": "confirmed"}, headers=auth_headers(TENANT))
    assert published_events[-1][1]["listing_confirmed_count"] == 2
    assert published_events[-1][1]["is_roommate_request"] is True
    assert published_events[-1][1]["listing_id"] == str(listing)

    await client.patch(f"{BASE}/{first['id']}/status", json={"status": "cancelled"}, headers=auth_headers(TENANT))
    assert published_events[-1][1]["listing_confirmed_count"] == 1


async def test_no_internal_endpoints_are_exposed(client, apartment):
    tenancy = apartment["tenancy"]
    assert (await client.get(f"/internal/v1/bookings/{tenancy['id']}/tenancy")).status_code == 404

