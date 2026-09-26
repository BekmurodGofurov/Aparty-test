import uuid

from tests.conftest import auth_headers, make_token

BASE = "/api/v1/notifications"
USER = 10


async def test_requires_a_valid_token(client):
    assert (await client.get(f"{BASE}/me")).status_code == 401
    for token in (make_token(USER, secret="another-secret-that-is-long-enough-32b"), make_token(USER, token_type="refresh"),
                  make_token(USER, aud="other"), make_token("admin")):
        response = await client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


async def test_empty_list(client):
    body = (await client.get(f"{BASE}/me", headers=auth_headers(USER))).json()
    assert body == {"notifications": [], "unread_count": 0}


async def test_list_has_the_fields_the_bell_needs(client, add_notification):
    await add_notification(USER, title="Yangi bron so'rovi", body="Details", target_url="/my-bookings")
    item = (await client.get(f"{BASE}/me", headers=auth_headers(USER))).json()["notifications"][0]
    assert set(item) == {"id", "type", "title", "body", "target_url", "is_read", "created_at"}
    assert (item["title"], item["body"], item["target_url"], item["is_read"]) == ("Yangi bron so'rovi", "Details", "/my-bookings", False)


async def test_only_own_notifications_newest_first(client, add_notification):
    await add_notification(USER, title="old", minutes_ago=30)
    await add_notification(USER, title="new", minutes_ago=1)
    await add_notification(USER + 1, title="someone else's")
    body = (await client.get(f"{BASE}/me", headers=auth_headers(USER))).json()
    assert [item["title"] for item in body["notifications"]] == ["new", "old"]
    assert body["unread_count"] == 2


async def test_limit_and_unread_only_keep_the_true_unread_count(client, add_notification):
    for index in range(5):
        await add_notification(USER, title=f"n{index}", minutes_ago=index)
    await add_notification(USER, title="read one", is_read=True, minutes_ago=10)

    limited = (await client.get(f"{BASE}/me", params={"limit": 2}, headers=auth_headers(USER))).json()
    assert len(limited["notifications"]) == 2
    assert limited["unread_count"] == 5

    unread = (await client.get(f"{BASE}/me", params={"unread_only": "true"}, headers=auth_headers(USER))).json()
    assert len(unread["notifications"]) == 5
    assert all(not item["is_read"] for item in unread["notifications"])


async def test_limit_is_validated(client):
    for value in (0, 101):
        assert (await client.get(f"{BASE}/me", params={"limit": value}, headers=auth_headers(USER))).status_code == 422


async def test_mark_one_read(client, add_notification):
    item = await add_notification(USER)
    response = await client.patch(f"{BASE}/{item.id}/read", headers=auth_headers(USER))
    assert response.status_code == 200
    assert response.json()["is_read"] is True
    again = await client.patch(f"{BASE}/{item.id}/read", headers=auth_headers(USER))
    assert again.status_code == 200
    assert (await client.get(f"{BASE}/me", headers=auth_headers(USER))).json()["unread_count"] == 0


async def test_cannot_read_someone_elses_or_unknown_notifications(client, add_notification):
    item = await add_notification(USER + 1)
    assert (await client.patch(f"{BASE}/{item.id}/read", headers=auth_headers(USER))).status_code == 404
    assert (await client.patch(f"{BASE}/{uuid.uuid4()}/read", headers=auth_headers(USER))).status_code == 404
    assert (await client.get(f"{BASE}/me", headers=auth_headers(USER + 1))).json()["unread_count"] == 1


async def test_mark_all_read_only_touches_the_callers_notifications(client, add_notification):
    await add_notification(USER)
    await add_notification(USER)
    await add_notification(USER, is_read=True)
    await add_notification(USER + 1)

    response = await client.patch(f"{BASE}/read-all", headers=auth_headers(USER))
    assert response.json() == {"updated": 2}
    assert (await client.get(f"{BASE}/me", headers=auth_headers(USER))).json()["unread_count"] == 0
    assert (await client.get(f"{BASE}/me", headers=auth_headers(USER + 1))).json()["unread_count"] == 1
    assert (await client.patch(f"{BASE}/read-all", headers=auth_headers(USER))).json() == {"updated": 0}
