from urllib.parse import parse_qs, urlsplit

from app.config import settings
from app.models import UserRole
from tests.conftest import AUTH_CODE, auth_headers, login_with_telegram, start_login

START = "/api/v1/auth/telegram/start"
CALLBACK = "/api/v1/auth/telegram/callback"


async def test_start_returns_url_and_binds_state_to_browser(client, fake_redis):
    response = await client.get(START)
    assert response.status_code == 200
    query = parse_qs(urlsplit(response.json()["authorization_url"]).query)
    state = query["state"][0]
    assert query["client_id"] == ["123456"]
    assert query["redirect_uri"] == [settings.telegram_redirect_uri]
    assert client.cookies.get("tg_login_state") == state
    assert await fake_redis.get(f"tg_login:{state}")


async def test_start_is_unavailable_when_telegram_is_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "telegram_client_secret", None)
    assert (await client.get(START)).status_code == 503


async def test_start_is_rate_limited_per_ip(client, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_per_minute", 2)
    headers = {"X-Real-IP": "203.0.113.7"}
    assert (await client.get(START, headers=headers)).status_code == 200
    assert (await client.get(START, headers=headers)).status_code == 200
    assert (await client.get(START, headers=headers)).status_code == 429
    assert (await client.get(START, headers={"X-Real-IP": "203.0.113.8"})).status_code == 200


async def test_first_login_creates_user_without_role(client, telegram):
    response = await login_with_telegram(client, telegram)
    assert response.status_code == 200
    body = response.json()
    assert body["needs_role"] is True
    assert body["user"]["id"] == 555001
    assert body["user"]["full_name"] == "Aziz Karimov"
    assert body["user"]["phone"] == "+998901234567"
    assert body["user"]["role"] is None
    assert body["user"]["telegram_username"] == "aziz"
    assert "refresh_token" in client.cookies
    assert "tg_login_state" not in client.cookies

    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["id"] == 555001


async def test_returning_login_keeps_edited_profile_and_role(client, telegram, create_user):
    await create_user(555001, role=UserRole.makler, full_name="Edited Name", phone="+998900000000")
    response = await login_with_telegram(client, telegram)
    body = response.json()
    assert body["needs_role"] is False
    assert body["user"]["full_name"] == "Edited Name"
    assert body["user"]["role"] == "makler"
    assert body["user"]["phone"] == "+998901234567"


async def test_callback_rejects_state_from_another_browser(client, telegram):
    state = await start_login(client, telegram)
    client.cookies.clear()
    response = await client.post(CALLBACK, json={"code": AUTH_CODE, "state": state})
    assert response.status_code == 400


async def test_callback_rejects_unknown_or_reused_state(client, telegram):
    state = await start_login(client, telegram)
    first = await client.post(CALLBACK, json={"code": AUTH_CODE, "state": state})
    assert first.status_code == 200

    client.cookies.set("tg_login_state", state)
    replay = await client.post(CALLBACK, json={"code": AUTH_CODE, "state": state})
    assert replay.status_code == 400

    client.cookies.set("tg_login_state", "forged")
    forged = await client.post(CALLBACK, json={"code": AUTH_CODE, "state": "forged"})
    assert forged.status_code == 400


async def test_callback_reports_telegram_rejection(client, telegram):
    state = await start_login(client, telegram)
    response = await client.post(CALLBACK, json={"code": "wrong-code", "state": state})
    assert response.status_code == 400
    assert "refresh_token" not in client.cookies


async def test_callback_rejects_wrong_pkce_verifier(client, telegram):
    state = await start_login(client, telegram)
    telegram.challenge = "some-other-challenge"
    assert (await client.post(CALLBACK, json={"code": AUTH_CODE, "state": state})).status_code == 400


async def test_callback_requires_phone(client, telegram):
    telegram.overrides = {"phone_number": None}
    response = await login_with_telegram(client, telegram)
    assert response.status_code == 400
    assert "phone" in response.json()["detail"].lower()


async def test_callback_rejects_phone_owned_by_another_account(client, telegram, create_user):
    await create_user(1, phone="+998901234567")
    assert (await login_with_telegram(client, telegram)).status_code == 409


async def test_callback_validates_body(client):
    assert (await client.post(CALLBACK, json={"code": ""})).status_code == 422
