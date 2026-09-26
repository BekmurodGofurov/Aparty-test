from app.clients.iam import PublicProfile
from tests.conftest import auth_headers

SEARCH = "/api/v1/listings/search"


async def test_search_returns_only_active_listings(client, create_listing):
    keep = await create_listing(owner_id=1)
    hidden = await create_listing(owner_id=1, title="Hidden one")
    await client.post(f"/api/v1/listings/{hidden['id']}/mark-occupied", headers=auth_headers(1))

    body = (await client.get(SEARCH)).json()
    assert [item["id"] for item in body["listings"]] == [keep["id"]]
    assert body["total"] == 1


async def test_search_filters(client, create_listing):
    await create_listing(price=1000000, district="Yunusobod", rooms_count=1, amenities={"wifi": True})
    await create_listing(price=3000000, district="Chilonzor", rooms_count=3, amenities={"wifi": False},
                         rental_type="shared_room")

    async def total(**params):
        return (await client.get(SEARCH, params=params)).json()["total"]

    assert await total() == 2
    assert await total(district="Chilonzor") == 1
    assert await total(price_min=2000000) == 1
    assert await total(price_max=2000000) == 1
    assert await total(rooms_count=2) == 1
    assert await total(rental_type="shared_room") == 1
    assert await total(wifi="true") == 1
    assert await total(wifi="false") == 1
    assert await total(district="Nowhere") == 0


async def test_search_owner_role_filter(client, create_listing):
    await create_listing(role="makler")
    await create_listing(role="owner")
    assert (await client.get(SEARCH, params={"owner_role": "makler"})).json()["total"] == 1
    assert (await client.get(SEARCH, params={"owner_role": "owner"})).json()["total"] == 1


async def test_search_pagination(client, create_listing):
    for index in range(5):
        await create_listing(title=f"Listing number {index}")
    first = (await client.get(SEARCH, params={"limit": 2, "page": 1})).json()
    last = (await client.get(SEARCH, params={"limit": 2, "page": 3})).json()
    assert (first["total"], first["pages"], len(first["listings"])) == (5, 3, 2)
    assert len(last["listings"]) == 1


async def test_search_empty_result_has_zero_pages(client):
    body = (await client.get(SEARCH)).json()
    assert (body["total"], body["pages"], body["listings"]) == (0, 0, [])


async def test_search_rejects_invalid_paging(client):
    assert (await client.get(SEARCH, params={"limit": 1000})).status_code == 422
    assert (await client.get(SEARCH, params={"page": 0})).status_code == 422


async def test_owner_details_come_from_iam(client, create_listing, iam_profiles):
    iam_profiles[1] = PublicProfile(id=1, full_name="Aziz Karimov", phone="+998901234567", is_verified=True)
    listing = await create_listing(owner_id=1)

    card = (await client.get(SEARCH)).json()["listings"][0]
    detail = (await client.get(f"/api/v1/listings/{listing['id']}")).json()
    for item in (card, detail):
        assert item["owner_full_name"] == "Aziz Karimov"
        assert item["owner_phone"] == "+998901234567"
        assert item["owner_verified"] is True


async def test_listing_is_served_when_iam_has_no_profile(client, create_listing):
    listing = await create_listing(owner_id=1)
    detail = (await client.get(f"/api/v1/listings/{listing['id']}")).json()
    assert detail["owner_full_name"] == ""
    assert detail["owner_phone"] is None
    assert detail["owner_verified"] is False
