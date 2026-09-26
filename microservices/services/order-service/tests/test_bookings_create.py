import asyncio

from tests.conftest import GUEST_ID, OWNER_ID, PRICE_PER_NIGHT, auth_headers, in_days

BASE = "/api/v1/bookings"


def payload(listing_id, start=5, end=8, **extra):
    return {"listing_id": str(listing_id), "start_date": in_days(start), "end_date": in_days(end), **extra}


async def test_create_requires_auth(client, catalog):
    assert (await client.post(BASE, json=payload(catalog.add()))).status_code == 401


async def test_create_booking_calculates_price_and_publishes_event(client, catalog, published_events):
    listing_id = catalog.add()
    response = await client.post(BASE, json=payload(listing_id, 5, 8, message="Hello"), headers=auth_headers(GUEST_ID))
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["user_id"] == GUEST_ID
    assert body["listing_owner_id"] == OWNER_ID
    assert body["total_price"] == 3 * PRICE_PER_NIGHT
    assert body["message"] == "Hello"
    assert published_events[0][0] == "booking.created"
    assert published_events[0][1]["booking_id"] == body["id"]
    assert published_events[0][1]["owner_id"] == OWNER_ID


async def test_create_rejects_invalid_dates(client, catalog):
    listing_id = catalog.add()
    for start, end in ((5, 5), (8, 5), (-2, 3)):
        response = await client.post(BASE, json=payload(listing_id, start, end), headers=auth_headers(GUEST_ID))
        assert response.status_code == 400, (start, end)


async def test_create_rejects_missing_or_unavailable_listing(client, catalog):
    unknown = await client.post(BASE, json=payload("00000000-0000-0000-0000-000000000000"), headers=auth_headers(GUEST_ID))
    assert unknown.status_code == 404
    for overrides in ({"status": "rented"}, {"status": "archived"}, {"is_active": False}):
        response = await client.post(BASE, json=payload(catalog.add(**overrides)), headers=auth_headers(GUEST_ID))
        assert response.status_code == 404, overrides


async def test_owner_cannot_book_own_listing(client, catalog):
    response = await client.post(BASE, json=payload(catalog.add()), headers=auth_headers(OWNER_ID))
    assert response.status_code == 400


async def test_create_reports_catalog_outage(client, catalog):
    listing_id = catalog.add()
    catalog.unavailable = True
    response = await client.post(BASE, json=payload(listing_id), headers=auth_headers(GUEST_ID))
    assert response.status_code == 503


async def test_overlapping_dates_conflict(client, catalog, create_booking):
    listing_id = catalog.add()
    await create_booking(listing_id, start=5, end=8)
    for start, end in ((5, 8), (6, 7), (4, 6), (7, 10), (1, 20)):
        response = await client.post(BASE, json=payload(listing_id, start, end), headers=auth_headers(30))
        assert response.status_code == 409, (start, end)


async def test_adjacent_dates_and_other_listings_are_allowed(client, catalog, create_booking):
    listing_id = catalog.add()
    await create_booking(listing_id, start=5, end=8)
    await create_booking(listing_id, guest_id=30, start=8, end=10)
    await create_booking(listing_id, guest_id=31, start=2, end=5)
    await create_booking(catalog.add(), guest_id=32, start=5, end=8)


async def test_cancelled_and_rejected_bookings_free_the_dates(client, catalog, create_booking):
    listing_id = catalog.add()
    first = await create_booking(listing_id, start=5, end=8)
    await client.patch(f"{BASE}/{first['id']}/status", json={"status": "cancelled"}, headers=auth_headers(GUEST_ID))
    second = await create_booking(listing_id, guest_id=30, start=5, end=8)
    await client.patch(f"{BASE}/{second['id']}/status", json={"status": "rejected"}, headers=auth_headers(OWNER_ID))
    await create_booking(listing_id, guest_id=31, start=5, end=8)


async def test_concurrent_requests_cannot_double_book(client, catalog):
    listing_id = catalog.add()
    responses = await asyncio.gather(
        *(client.post(BASE, json=payload(listing_id), headers=auth_headers(guest)) for guest in (30, 31, 32))
    )
    assert sorted(r.status_code for r in responses) == [201, 409, 409]


async def test_booking_requires_a_chosen_role(client, catalog):
    body = payload(catalog.add())
    assert (await client.post(BASE, json=body, headers=auth_headers(GUEST_ID, None))).status_code == 403
    assert (await client.post(BASE, json=body, headers=auth_headers(GUEST_ID, "admin"))).status_code == 403
    for role in ("student", "owner", "makler"):
        listing_body = payload(catalog.add(), start=5 + 10, end=8 + 10)
        assert (await client.post(BASE, json=listing_body, headers=auth_headers(GUEST_ID, role))).status_code == 201, role
