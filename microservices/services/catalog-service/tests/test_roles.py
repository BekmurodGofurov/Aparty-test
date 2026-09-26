import pytest

from tests.conftest import LISTING_PAYLOAD, auth_headers, make_token

LISTINGS = "/api/v1/listings"
UPLOAD = "/api/v1/media/upload"


@pytest.mark.parametrize("role", ["owner", "makler"])
async def test_owners_and_maklers_can_create_listings(client, role):
    response = await client.post(LISTINGS, json=LISTING_PAYLOAD, headers=auth_headers(1, role))
    assert response.status_code == 201


@pytest.mark.parametrize("role", ["student", "admin"])
async def test_other_roles_cannot_create_listings(client, role):
    response = await client.post(LISTINGS, json=LISTING_PAYLOAD, headers=auth_headers(1, role))
    assert response.status_code == 403


async def test_user_without_a_role_cannot_create_listings(client):
    response = await client.post(LISTINGS, json=LISTING_PAYLOAD, headers=auth_headers(1, None))
    assert response.status_code == 403
    assert "role" in response.json()["detail"].lower()


async def test_listing_source_follows_the_role_not_the_request(client):
    as_owner = await client.post(LISTINGS, json={**LISTING_PAYLOAD, "source": "makler"}, headers=auth_headers(1, "owner"))
    as_makler = await client.post(LISTINGS, json={**LISTING_PAYLOAD, "source": "owner"}, headers=auth_headers(2, "makler"))
    assert as_owner.json()["source"] == "owner"
    assert as_owner.json()["owner_role"] == "owner"
    assert as_makler.json()["source"] == "makler"
    assert as_makler.json()["owner_role"] == "makler"


async def test_source_cannot_be_changed_by_update(client, create_listing):
    listing = await create_listing(owner_id=1, role="owner")
    response = await client.patch(f"{LISTINGS}/{listing['id']}", json={"source": "makler"}, headers=auth_headers(1, "owner"))
    assert response.json()["source"] == "owner"


async def test_own_listings_stay_manageable_regardless_of_role_claim(client, create_listing):
    listing = await create_listing(owner_id=1)
    response = await client.patch(f"{LISTINGS}/{listing['id']}", json={"price": 5}, headers=auth_headers(1, "owner"))
    assert response.status_code == 200


async def test_media_upload_needs_a_chosen_role(client):
    files = {"file": ("a.txt", b"x", "text/plain")}
    no_role = await client.post(UPLOAD, files=files, headers=auth_headers(1, None))
    assert no_role.status_code == 403
    student = await client.post(UPLOAD, files=files, headers=auth_headers(1, "student"))
    assert student.status_code == 400  # allowed through the role check, rejected by file validation
