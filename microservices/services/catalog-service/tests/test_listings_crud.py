from tests.conftest import LISTING_PAYLOAD, auth_headers

BASE = "/api/v1/listings"


async def test_create_requires_auth(client):
    assert (await client.post(BASE, json=LISTING_PAYLOAD)).status_code == 401


async def test_create_listing_sets_owner_and_images(client, published_events):
    response = await client.post(
        BASE,
        json={**LISTING_PAYLOAD, "images": ["https://cdn.test/a.jpg", {"url": "https://cdn.test/b.jpg"}]},
        headers=auth_headers(42),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["owner_id"] == 42
    assert body["status"] == "active"
    assert body["images"] == ["https://cdn.test/a.jpg", "https://cdn.test/b.jpg"]
    assert [key for key, _ in published_events] == ["listing.created"]
    assert published_events[0][1]["id"] == body["id"]


async def test_create_without_title_builds_one_from_location(client):
    payload = {k: v for k, v in LISTING_PAYLOAD.items() if k != "title"}
    response = await client.post(BASE, json=payload, headers=auth_headers(1))
    assert response.json()["title"] == "Yunusobod, Toshkent shahri, Amir Temur 1"


async def test_create_rejects_invalid_price_and_image(client):
    assert (await client.post(BASE, json={**LISTING_PAYLOAD, "price": 0}, headers=auth_headers(1))).status_code == 422
    bad_image = await client.post(BASE, json={**LISTING_PAYLOAD, "images": [{}]}, headers=auth_headers(1))
    assert bad_image.status_code == 422


async def test_get_listing_counts_views(client, create_listing):
    listing = await create_listing()
    await client.get(f"{BASE}/{listing['id']}")
    second = await client.get(f"{BASE}/{listing['id']}")
    assert second.json()["views_count"] == 2


async def test_get_unknown_listing_is_404(client):
    response = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_my_listings_returns_only_own(client, create_listing):
    await create_listing(owner_id=1)
    await create_listing(owner_id=2)
    response = await client.get(f"{BASE}/me", headers=auth_headers(1))
    assert [item["owner_id"] for item in response.json()] == [1]


async def test_update_by_owner(client, create_listing, published_events):
    listing = await create_listing(owner_id=1)
    response = await client.patch(
        f"{BASE}/{listing['id']}", json={"price": 2000000, "images": ["https://cdn.test/new.jpg"]},
        headers=auth_headers(1),
    )
    assert response.status_code == 200
    assert response.json()["price"] == 2000000
    assert response.json()["images"] == ["https://cdn.test/new.jpg"]
    assert published_events[-1][0] == "listing.updated"


async def test_update_location_keeps_title(client, create_listing):
    listing = await create_listing(owner_id=1)
    response = await client.patch(f"{BASE}/{listing['id']}", json={"district": "Chilonzor"}, headers=auth_headers(1))
    assert response.json()["title"] == LISTING_PAYLOAD["title"]
    assert response.json()["district"] == "Chilonzor"


async def test_update_and_delete_by_other_user_are_forbidden(client, create_listing):
    listing = await create_listing(owner_id=1)
    assert (await client.put(f"{BASE}/{listing['id']}", json={"price": 1}, headers=auth_headers(2))).status_code == 403
    assert (await client.delete(f"{BASE}/{listing['id']}", headers=auth_headers(2))).status_code == 403


async def test_delete_is_soft_and_hides_listing(client, create_listing, published_events):
    listing = await create_listing(owner_id=1)
    deleted = await client.delete(f"{BASE}/{listing['id']}", headers=auth_headers(1))
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"
    assert (await client.get(f"{BASE}/{listing['id']}")).status_code == 404
    assert (await client.get(f"{BASE}/me", headers=auth_headers(1))).json() == []
    assert published_events[-1][1]["status"] == "deleted"


async def test_mark_occupied_and_available(client, create_listing):
    listing = await create_listing(owner_id=1, max_guests=3)
    occupied = await client.post(f"{BASE}/{listing['id']}/mark-occupied", headers=auth_headers(1))
    assert occupied.status_code == 200
    assert (await client.get(f"{BASE}/{listing['id']}")).json()["status"] == "rented"

    await client.post(f"{BASE}/{listing['id']}/mark-available", headers=auth_headers(1))
    body = (await client.get(f"{BASE}/{listing['id']}")).json()
    assert body["status"] == "active"
    assert body["available_spaces"] == 3


async def test_status_actions_require_ownership(client, create_listing):
    listing = await create_listing(owner_id=1)
    for action in ("activate-basic", "mark-occupied", "mark-available"):
        response = await client.post(f"{BASE}/{listing['id']}/{action}", headers=auth_headers(2))
        assert response.status_code == 403, action


async def test_booking_info_does_not_count_a_view(client, create_listing):
    listing = await create_listing(owner_id=5, price=900000)
    info = await client.get(f"{BASE}/{listing['id']}/booking-info")
    assert info.status_code == 200
    assert info.json() == {
        "id": listing["id"],
        "owner_id": 5,
        "title": listing["title"],
        "price": 900000,
        "status": "active",
        "is_active": True,
        "rental_type": "full_unit",
        "available_spaces": 1,
        "parent_listing_id": None,
    }
    assert (await client.get(f"{BASE}/{listing['id']}")).json()["views_count"] == 1


async def test_booking_info_hides_deleted_listing(client, create_listing):
    listing = await create_listing(owner_id=1)
    await client.delete(f"{BASE}/{listing['id']}", headers=auth_headers(1))
    assert (await client.get(f"{BASE}/{listing['id']}/booking-info")).status_code == 404
