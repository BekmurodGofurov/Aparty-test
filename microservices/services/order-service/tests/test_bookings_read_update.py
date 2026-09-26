import pytest

from tests.conftest import GUEST_ID, OWNER_ID, auth_headers

BASE = "/api/v1/bookings"


async def test_guest_lists_only_own_bookings(client, create_booking):
    mine = await create_booking(guest_id=GUEST_ID)
    await create_booking(guest_id=30)
    response = await client.get(BASE, headers=auth_headers(GUEST_ID))
    assert [item["id"] for item in response.json()] == [mine["id"]]


async def test_owner_lists_incoming_bookings_and_filters_by_listing(client, catalog, create_booking):
    first_listing, second_listing = catalog.add(), catalog.add()
    first = await create_booking(first_listing, guest_id=30)
    second = await create_booking(second_listing, guest_id=31)
    await create_booking(catalog.add(owner_id=99), guest_id=32)

    everything = await client.get(f"{BASE}/incoming", headers=auth_headers(OWNER_ID))
    assert {item["id"] for item in everything.json()} == {first["id"], second["id"]}

    filtered = await client.get(f"{BASE}/incoming", params={"listing_id": str(first_listing)}, headers=auth_headers(OWNER_ID))
    assert [item["id"] for item in filtered.json()] == [first["id"]]


async def test_guest_cannot_see_incoming_bookings_of_others(client, create_booking):
    await create_booking()
    response = await client.get(f"{BASE}/incoming", headers=auth_headers(GUEST_ID))
    assert response.json() == []


async def test_get_booking_access(client, create_booking):
    booking = await create_booking()
    for user_id, expected in ((GUEST_ID, 200), (OWNER_ID, 200), (77, 403)):
        response = await client.get(f"{BASE}/{booking['id']}", headers=auth_headers(user_id))
        assert response.status_code == expected, user_id
    missing = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000", headers=auth_headers(GUEST_ID))
    assert missing.status_code == 404


@pytest.mark.parametrize("target", ["confirmed", "rejected", "cancelled"])
async def test_owner_can_resolve_pending_booking(client, create_booking, published_events, target):
    booking = await create_booking()
    response = await client.patch(f"{BASE}/{booking['id']}/status", json={"status": target}, headers=auth_headers(OWNER_ID))
    assert response.status_code == 200
    assert response.json()["status"] == target
    assert published_events[-1][0] == "booking.updated"
    assert published_events[-1][1]["status"] == target


async def test_owner_can_cancel_confirmed_booking(client, create_booking):
    booking = await create_booking()
    await client.patch(f"{BASE}/{booking['id']}/status", json={"status": "confirmed"}, headers=auth_headers(OWNER_ID))
    response = await client.patch(f"{BASE}/{booking['id']}/status", json={"status": "cancelled"}, headers=auth_headers(OWNER_ID))
    assert response.json()["status"] == "cancelled"


async def test_guest_can_only_cancel(client, create_booking):
    booking = await create_booking()
    url = f"{BASE}/{booking['id']}/status"
    for target in ("confirmed", "rejected", "pending"):
        assert (await client.patch(url, json={"status": target}, headers=auth_headers(GUEST_ID))).status_code == 409, target
    cancelled = await client.patch(url, json={"status": "cancelled"}, headers=auth_headers(GUEST_ID))
    assert cancelled.status_code == 200


async def test_finalized_bookings_cannot_change(client, create_booking):
    booking = await create_booking()
    url = f"{BASE}/{booking['id']}/status"
    await client.patch(url, json={"status": "rejected"}, headers=auth_headers(OWNER_ID))
    for target in ("confirmed", "cancelled", "pending"):
        assert (await client.patch(url, json={"status": target}, headers=auth_headers(OWNER_ID))).status_code == 409, target


async def test_stranger_cannot_change_status(client, create_booking):
    booking = await create_booking()
    response = await client.patch(f"{BASE}/{booking['id']}/status", json={"status": "confirmed"}, headers=auth_headers(77))
    assert response.status_code == 403
