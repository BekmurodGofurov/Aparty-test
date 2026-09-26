from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.config import settings
from tests.conftest import LISTING_PAYLOAD, auth_headers

LISTINGS = "/api/v1/listings"
STUDENT = 20
OWNER = 1


@pytest.fixture
async def apartment(create_listing):
    return await create_listing(owner_id=OWNER, images=["https://cdn.test/a.jpg", "https://cdn.test/b.jpg"])


def ad_body(**overrides):
    body = {"residents_male": 2, "residents_female": 1, "residents_children": 0, "available_spaces": 1,
            "target_gender": "female", "price": 700000}
    return {**body, **overrides}


async def post_ad(client, apartment_id, user_id=STUDENT, role="student", **overrides):
    return await client.post(f"{LISTINGS}/{apartment_id}/roommate", json=ad_body(**overrides), headers=auth_headers(user_id, role))


async def test_tenant_posts_an_ad_without_booking_or_owner_permission(client, apartment, published_events):
    response = await post_ad(client, apartment["id"], description="Quiet flat, we cook together",
                             available_from="2030-01-15", target_gender="female", available_spaces=2)
    assert response.status_code == 201
    ad = response.json()
    assert ad["owner_id"] == STUDENT
    assert ad["source"] == "roommate"
    assert ad["owner_role"] == "student"
    assert ad["rental_type"] == "shared_room"
    assert ad["parent_listing_id"] == apartment["id"]
    assert (ad["residents_male"], ad["residents_female"], ad["residents_children"]) == (2, 1, 0)
    assert ad["target_gender"] == "female"
    assert ad["available_spaces"] == 2
    assert ad["available_from"] == "2030-01-15"
    assert ad["price"] == 700000
    assert ad["title"] == f"Roommate wanted: {apartment['title']}"


async def test_ad_lasts_thirty_days(client, apartment):
    ad = (await post_ad(client, apartment["id"])).json()
    expires = datetime.fromisoformat(ad["expires_at"])
    remaining = expires - datetime.now(timezone.utc)
    assert timedelta(days=settings.roommate_listing_days - 1) < remaining <= timedelta(days=settings.roommate_listing_days)
    assert settings.roommate_listing_days == 30


async def test_ad_without_a_date_means_anytime(client, apartment):
    ad = (await post_ad(client, apartment["id"])).json()
    assert ad["available_from"] is None


async def test_location_photos_and_amenities_come_from_the_apartment(client, apartment):
    ad = (await post_ad(client, apartment["id"])).json()
    for field in ("region", "district", "address", "latitude", "longitude", "rooms_count"):
        assert ad[field] == apartment[field], field
    assert ad["images"] == ["https://cdn.test/a.jpg", "https://cdn.test/b.jpg"]
    assert ad["amenities"] == LISTING_PAYLOAD["amenities"]


async def test_event_tells_who_owns_the_apartment(client, apartment, published_events):
    ad = (await post_ad(client, apartment["id"])).json()
    routing_key, payload = published_events[-1]
    assert routing_key == "listing.created"
    assert payload["id"] == ad["id"]
    assert payload["source"] == "roommate"
    assert payload["parent_listing_id"] == apartment["id"]
    assert payload["apartment_owner_id"] == OWNER
    assert payload["owner_id"] == STUDENT


@pytest.mark.parametrize("role", ["student", "makler"])
async def test_tenants_can_post(client, apartment, role):
    assert (await post_ad(client, apartment["id"], role=role)).status_code == 201


@pytest.mark.parametrize("role", ["owner", "admin", None])
async def test_owners_admins_and_users_without_a_role_cannot_post(client, apartment, role):
    assert (await post_ad(client, apartment["id"], role=role)).status_code == 403


async def test_posting_requires_login(client, apartment):
    response = await client.post(f"{LISTINGS}/{apartment['id']}/roommate", json=ad_body())
    assert response.status_code == 401


async def test_the_apartment_owner_cannot_post_for_their_own_apartment(client, create_listing):
    apartment = await create_listing(owner_id=OWNER, role="makler")
    assert (await post_ad(client, apartment["id"], user_id=OWNER, role="makler")).status_code == 403


async def test_ad_can_be_posted_for_a_rented_apartment(client, apartment):
    await client.post(f"{LISTINGS}/{apartment['id']}/mark-occupied", headers=auth_headers(OWNER))
    assert (await post_ad(client, apartment["id"])).status_code == 201


async def test_apartment_must_exist_and_must_not_be_an_ad(client, apartment):
    assert (await post_ad(client, "00000000-0000-0000-0000-000000000000")).status_code == 404
    ad = (await post_ad(client, apartment["id"])).json()
    assert (await post_ad(client, ad["id"], user_id=30)).status_code == 409

    await client.delete(f"{LISTINGS}/{apartment['id']}", headers=auth_headers(OWNER))
    assert (await post_ad(client, apartment["id"], user_id=31)).status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [{"available_spaces": 0}, {"available_spaces": 11}, {"residents_male": -1}, {"residents_children": 21}, {"price": 0}],
    ids=["no-places", "too-many-places", "negative-residents", "too-many-residents", "no-price"],
)
async def test_invalid_ads_are_rejected(client, apartment, overrides):
    assert (await post_ad(client, apartment["id"], **overrides)).status_code == 422


async def test_an_apartment_has_one_active_ad(client, apartment, create_listing):
    other = await create_listing(owner_id=2)
    assert (await post_ad(client, apartment["id"])).status_code == 201
    assert (await post_ad(client, apartment["id"])).status_code == 409
    assert (await post_ad(client, apartment["id"], user_id=STUDENT + 1)).status_code == 409
    assert (await post_ad(client, other["id"])).status_code == 201  # the same person, another apartment


async def test_closing_or_expiry_allows_a_new_ad_for_the_apartment(client, apartment, engine):
    first = (await post_ad(client, apartment["id"])).json()
    await client.delete(f"{LISTINGS}/{first['id']}", headers=auth_headers(STUDENT, "student"))
    second = (await post_ad(client, apartment["id"], user_id=STUDENT + 1)).json()
    assert second["id"] != first["id"]

    async with engine.begin() as conn:
        await conn.execute(text("UPDATE listings SET expires_at = now() - interval '1 day' WHERE id = :id"), {"id": second["id"]})
    third = await post_ad(client, apartment["id"])
    assert third.status_code == 201
    assert (await client.get(f"{LISTINGS}/{second['id']}/booking-info")).json()["status"] == "archived"


async def test_a_full_ad_still_counts_until_it_is_closed(client, apartment):
    ad = (await post_ad(client, apartment["id"])).json()
    await client.post(f"{LISTINGS}/{ad['id']}/mark-occupied", headers=auth_headers(STUDENT, "student"))
    assert (await post_ad(client, apartment["id"], user_id=STUDENT + 1)).status_code == 409


async def test_simultaneous_posts_create_a_single_ad(client, apartment):
    import asyncio

    responses = await asyncio.gather(*(post_ad(client, apartment["id"], user_id=STUDENT + n) for n in range(4)))
    assert sorted(r.status_code for r in responses) == [201, 409, 409, 409]


async def test_ads_appear_in_student_search_with_who_lives_there(client, apartment):
    await post_ad(client, apartment["id"], residents_male=1, residents_female=2, residents_children=1)
    cards = (await client.get(f"{LISTINGS}/search", params={"owner_role": "student"})).json()["listings"]
    assert len(cards) == 1
    assert (cards[0]["residents_male"], cards[0]["residents_female"], cards[0]["residents_children"]) == (1, 2, 1)
    assert cards[0]["parent_listing_id"] == apartment["id"]
    assert cards[0]["target_gender"] == "female"
    assert (await client.get(f"{LISTINGS}/search", params={"target_gender": "female", "rental_type": "shared_room"})).json()["total"] == 1


async def test_expired_ads_disappear_from_search_and_cannot_be_booked(client, apartment, engine):
    ad = (await post_ad(client, apartment["id"])).json()
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE listings SET expires_at = now() - interval '1 minute' WHERE id = :id"), {"id": ad["id"]})
    found = (await client.get(f"{LISTINGS}/search")).json()["listings"]
    assert [card["id"] for card in found] == [apartment["id"]]
    assert (await client.get(f"{LISTINGS}/{ad['id']}/booking-info")).json()["is_active"] is False


async def test_the_poster_can_edit_the_ad_but_not_the_location(client, apartment):
    ad = (await post_ad(client, apartment["id"])).json()
    url = f"{LISTINGS}/{ad['id']}"
    ok = await client.patch(url, json={"price": 600000, "description": "Updated", "available_spaces": 2, "residents_male": 1,
                                       "available_from": "2030-02-01"}, headers=auth_headers(STUDENT, "student"))
    assert ok.status_code == 200
    body = ok.json()
    assert (body["price"], body["description"], body["available_spaces"], body["residents_male"]) == (600000, "Updated", 2, 1)
    assert body["available_from"] == "2030-02-01"

    for field, value in (("address", "Elsewhere 5"), ("latitude", 1.0), ("rooms_count", 9)):
        assert (await client.patch(url, json={field: value}, headers=auth_headers(STUDENT, "student"))).status_code == 422, field
    for spaces in (0, 11):
        assert (await client.patch(url, json={"available_spaces": spaces}, headers=auth_headers(STUDENT, "student"))).status_code == 422


async def test_only_the_poster_manages_the_ad(client, apartment):
    ad = (await post_ad(client, apartment["id"])).json()
    url = f"{LISTINGS}/{ad['id']}"
    for user_id, role in ((OWNER, "owner"), (99, "student")):
        assert (await client.patch(url, json={"price": 1}, headers=auth_headers(user_id, role))).status_code == 403
        assert (await client.delete(url, headers=auth_headers(user_id, role))).status_code == 403


async def test_deleting_the_apartment_closes_its_ads(client, apartment):
    ad = (await post_ad(client, apartment["id"])).json()
    await client.delete(f"{LISTINGS}/{apartment['id']}", headers=auth_headers(OWNER))
    assert (await client.get(f"{LISTINGS}/search")).json()["total"] == 0
    assert (await client.get(f"{LISTINGS}/{ad['id']}/booking-info")).json()["status"] == "archived"


async def test_booking_info_points_to_the_apartment_and_the_offered_places(client, apartment):
    ad = (await post_ad(client, apartment["id"], available_spaces=3)).json()
    info = (await client.get(f"{LISTINGS}/{ad['id']}/booking-info")).json()
    assert info["parent_listing_id"] == apartment["id"]
    assert info["available_spaces"] == 3
    assert info["rental_type"] == "shared_room"
    assert info["owner_id"] == STUDENT


async def test_students_still_cannot_create_ordinary_listings(client):
    assert (await client.post(LISTINGS, json=LISTING_PAYLOAD, headers=auth_headers(STUDENT, "student"))).status_code == 403
