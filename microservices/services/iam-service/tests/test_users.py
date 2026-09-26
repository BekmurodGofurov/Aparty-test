import jwt

from app.models import UserRole
from tests.conftest import auth_headers


async def test_me_requires_token(client):
    assert (await client.get("/api/v1/users/me")).status_code == 401


async def test_me_returns_profile(client, create_user):
    await create_user(1, full_name="Aziz Karimov")
    response = await client.get("/api/v1/users/me", headers=auth_headers(1))
    assert response.status_code == 200
    assert response.json()["full_name"] == "Aziz Karimov"


async def test_update_profile_supports_english_and_uzbek_keys(client, create_user):
    await create_user(1)
    response = await client.put(
        "/api/v1/users/me", json={"ism": "Yangi Ism", "university": "Sharda"}, headers=auth_headers(1)
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Yangi Ism"
    assert response.json()["university"] == "Sharda"


async def test_phone_cannot_be_changed(client, create_user):
    user = await create_user(1)
    response = await client.put(
        "/api/v1/users/me", json={"phone": "+998911111111", "telefon": "+998922222222"}, headers=auth_headers(1)
    )
    assert response.status_code == 200
    assert response.json()["phone"] == user.phone


async def test_role_can_be_chosen_once_and_token_carries_it(client, create_user):
    await create_user(1, role=None)
    response = await client.put("/api/v1/users/me/role", json={"role": "makler"}, headers=auth_headers(1, None))
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "makler"
    claims = jwt.decode(response.json()["access_token"], options={"verify_signature": False})
    assert claims["role"] == "makler"

    again = await client.put("/api/v1/users/me/role", json={"role": "owner"}, headers=auth_headers(1, "makler"))
    assert again.status_code == 409


async def test_admin_role_cannot_be_selected(client, create_user):
    await create_user(1, role=None)
    response = await client.put("/api/v1/users/me/role", json={"role": "admin"}, headers=auth_headers(1, None))
    assert response.status_code == 422


async def test_get_user_by_id_permissions(client, create_user):
    await create_user(1)
    await create_user(2)
    assert (await client.get("/api/v1/users/1", headers=auth_headers(1))).status_code == 200
    assert (await client.get("/api/v1/users/2", headers=auth_headers(1))).status_code == 403
    assert (await client.get("/api/v1/users/999", headers=auth_headers(1))).status_code == 403
    assert (await client.get("/api/v1/users/2", headers=auth_headers("admin", "admin"))).status_code == 200


async def test_public_profiles_expose_only_contact_safe_fields(client, create_user):
    await create_user(1, full_name="Aziz Karimov", role=UserRole.owner, university="Secret Uni")
    await create_user(2, full_name="Malika", is_verified=False)

    response = await client.get("/api/v1/users/public", params={"ids": "1,2,999"})
    assert response.status_code == 200
    by_id = {item["id"]: item for item in response.json()}
    assert set(by_id) == {1, 2}
    assert by_id[1] == {"id": 1, "full_name": "Aziz Karimov", "phone": "+998900000001", "is_verified": True}
    assert by_id[2]["is_verified"] is False


async def test_public_profiles_validate_ids(client):
    assert (await client.get("/api/v1/users/public", params={"ids": "abc"})).status_code == 422
    assert (await client.get("/api/v1/users/public", params={"ids": ""})).json() == []
    too_many = ",".join(str(i) for i in range(1, 102))
    assert (await client.get("/api/v1/users/public", params={"ids": too_many})).status_code == 422
    assert (await client.get("/api/v1/users/public")).status_code == 422
