from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME, auth_headers, login_with_telegram

REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ADMIN_LOGIN = "/api/v1/auth/admin-login"


async def test_refresh_rotates_the_token_and_old_one_stops_working(client, telegram):
    await login_with_telegram(client, telegram)
    first_cookie = client.cookies.get("refresh_token")

    refreshed = await client.post(REFRESH)
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    assert client.cookies.get("refresh_token") != first_cookie

    client.cookies.set("refresh_token", first_cookie)
    assert (await client.post(REFRESH)).status_code == 401


async def test_refresh_picks_up_a_newly_chosen_role(client, telegram):
    login = await login_with_telegram(client, telegram)
    token = login.json()["access_token"]
    await client.put("/api/v1/users/me/role", json={"role": "owner"}, headers={"Authorization": f"Bearer {token}"})

    new_token = (await client.post(REFRESH)).json()["access_token"]
    import jwt
    assert jwt.decode(new_token, options={"verify_signature": False})["role"] == "owner"


async def test_refresh_requires_a_valid_session(client):
    assert (await client.post(REFRESH)).status_code == 401
    client.cookies.set("refresh_token", "made-up-token")
    assert (await client.post(REFRESH)).status_code == 401


async def test_refresh_token_in_body_is_ignored(client, telegram):
    await login_with_telegram(client, telegram)
    token = client.cookies.get("refresh_token")
    client.cookies.clear()
    assert (await client.post(REFRESH, json={"refresh_token": token})).status_code == 401


async def test_refresh_rejects_deleted_user(client, telegram, engine):
    from sqlalchemy import text

    await login_with_telegram(client, telegram)
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM users"))
    assert (await client.post(REFRESH)).status_code == 401


async def test_logout_revokes_the_session(client, telegram):
    await login_with_telegram(client, telegram)
    token = client.cookies.get("refresh_token")

    assert (await client.post(LOGOUT)).json()["success"] is True
    client.cookies.set("refresh_token", token)
    assert (await client.post(REFRESH)).status_code == 401


async def test_logout_without_session_still_succeeds(client):
    assert (await client.post(LOGOUT)).status_code == 200


async def test_admin_login_and_refresh(client):
    login = await client.post(ADMIN_LOGIN, json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD})
    assert login.status_code == 200
    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.json()["role"] == "admin"

    refreshed = await client.post(REFRESH)
    assert refreshed.status_code == 200
    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"})
    assert me.json()["role"] == "admin"


async def test_admin_login_locks_after_repeated_failures(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_login_max_failures", 3)
    bad = {"username": TEST_ADMIN_USERNAME, "password": "wrong"}
    for _ in range(3):
        assert (await client.post(ADMIN_LOGIN, json=bad)).status_code == 401

    good = {"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD}
    assert (await client.post(ADMIN_LOGIN, json=good)).status_code == 429
    other_ip = await client.post(ADMIN_LOGIN, json=good, headers={"X-Real-IP": "198.51.100.9"})
    assert other_ip.status_code == 200


async def test_admin_failures_reset_after_success(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_login_max_failures", 3)
    bad = {"username": TEST_ADMIN_USERNAME, "password": "wrong"}
    good = {"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD}
    for _ in range(2):
        await client.post(ADMIN_LOGIN, json=bad)
    assert (await client.post(ADMIN_LOGIN, json=good)).status_code == 200
    for _ in range(2):
        assert (await client.post(ADMIN_LOGIN, json=bad)).status_code == 401
