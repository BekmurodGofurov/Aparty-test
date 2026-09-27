import uuid

from sqlalchemy import text

from app.clients.iam import PublicProfile
from tests.conftest import auth_headers

FAVORITES = "/api/v1/favorites"
SEARCH = "/api/v1/listings/search"
STUDENT = 20


async def toggle(client, listing_id, user_id=STUDENT, role="student"):
    return await client.post(f"{FAVORITES}/{listing_id}", headers=auth_headers(user_id, role))


async def my_favorites(client, user_id=STUDENT, role="student"):
    response = await client.get(f"{FAVORITES}/me", headers=auth_headers(user_id, role))
    assert response.status_code == 200
    return response.json()


async def test_toggle_saves_then_removes(client, create_listing):
    listing = await create_listing()

    assert (await toggle(client, listing["id"])).json() == {"status": "added"}
    saved = await my_favorites(client)
    assert [item["id"] for item in saved] == [listing["id"]]
    assert saved[0]["is_favorite"] is True

    assert (await toggle(client, listing["id"])).json() == {"status": "removed"}
    assert await my_favorites(client) == []


async def test_favorites_are_private_to_each_user(client, create_listing):
    listing = await create_listing()
    await toggle(client, listing["id"], user_id=STUDENT)
    assert await my_favorites(client, user_id=21) == []


async def test_most_recently_saved_comes_first(client, create_listing):
    first = await create_listing(title="First flat")
    second = await create_listing(title="Second flat")
    await toggle(client, first["id"])
    await toggle(client, second["id"])
    assert [item["id"] for item in await my_favorites(client)] == [second["id"], first["id"]]


async def test_owners_and_maklers_can_save_too(client, create_listing):
    listing = await create_listing(owner_id=1)
    for user_id, role in ((2, "owner"), (3, "makler")):
        assert (await toggle(client, listing["id"], user_id=user_id, role=role)).json() == {"status": "added"}


async def test_unknown_or_deleted_listing_is_404(client, create_listing):
    assert (await toggle(client, uuid.uuid4())).status_code == 404

    listing = await create_listing(owner_id=1)
    await client.delete(f"/api/v1/listings/{listing['id']}", headers=auth_headers(1))
    assert (await toggle(client, listing["id"])).status_code == 404


async def test_deleted_listing_disappears_from_favorites_and_can_be_unsaved(client, create_listing):
    listing = await create_listing(owner_id=1)
    await toggle(client, listing["id"])
    await client.delete(f"/api/v1/listings/{listing['id']}", headers=auth_headers(1))

    assert await my_favorites(client) == []
    assert (await toggle(client, listing["id"])).json() == {"status": "removed"}


async def test_favorites_require_login_and_a_role(client, create_listing):
    listing = await create_listing()
    assert (await client.post(f"{FAVORITES}/{listing['id']}")).status_code == 401
    assert (await client.get(f"{FAVORITES}/me")).status_code == 401
    assert (await toggle(client, listing["id"], role=None)).status_code == 403


async def test_favorite_row_is_removed_with_its_listing(client, create_listing, db_session):
    listing = await create_listing()
    await toggle(client, listing["id"])
    await db_session.execute(text("DELETE FROM listings WHERE id = :id"), {"id": listing["id"]})
    await db_session.commit()
    count = (await db_session.execute(text("SELECT count(*) FROM favorites"))).scalar_one()
    assert count == 0


async def test_favorites_carry_owner_contact(client, create_listing, iam_profiles):
    iam_profiles[1] = PublicProfile(id=1, full_name="Aziz", phone="+998901234567", telegram_username="aziz", is_verified=True)
    listing = await create_listing(owner_id=1)
    await toggle(client, listing["id"])
    card = (await my_favorites(client))[0]
    assert card["owner_telegram_url"] == "https://t.me/aziz"
    assert card["owner_phone"] == "+998901234567"


async def test_search_marks_the_users_saved_listings(client, create_listing):
    saved = await create_listing(title="Saved flat")
    other = await create_listing(title="Other flat")
    await toggle(client, saved["id"])

    cards = {item["id"]: item for item in (await client.get(SEARCH, headers=auth_headers(STUDENT, "student"))).json()["listings"]}
    assert cards[saved["id"]]["is_favorite"] is True
    assert cards[other["id"]]["is_favorite"] is False


async def test_search_stays_public_and_ignores_a_bad_token(client, create_listing):
    listing = await create_listing()
    await toggle(client, listing["id"])

    anonymous = await client.get(SEARCH)
    assert anonymous.status_code == 200
    assert anonymous.json()["listings"][0]["is_favorite"] is False

    bad_token = await client.get(SEARCH, headers={"Authorization": "Bearer not-a-token"})
    assert bad_token.status_code == 200
    assert bad_token.json()["listings"][0]["is_favorite"] is False


async def test_listing_detail_says_whether_the_user_saved_it(client, create_listing):
    listing = await create_listing()
    url = f"/api/v1/listings/{listing['id']}"
    await toggle(client, listing["id"])

    saved = await client.get(url, headers=auth_headers(STUDENT, "student"))
    assert saved.json()["is_favorite"] is True
    assert (await client.get(url, headers=auth_headers(21, "student"))).json()["is_favorite"] is False
    assert (await client.get(url)).json()["is_favorite"] is False
