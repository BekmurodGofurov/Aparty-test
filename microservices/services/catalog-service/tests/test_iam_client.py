import httpx

from app.clients.iam import fetch_public_profiles
from tests.helpers import mock_outbound_http


async def test_fetch_public_profiles_returns_profiles_by_id(monkeypatch):
    def handler(request):
        assert request.url.path == "/api/v1/users/public"
        assert request.url.params["ids"] == "1,2"
        return httpx.Response(200, json=[
            {"id": 1, "full_name": "Aziz", "phone": "+998900000001", "is_verified": True},
            {"id": 2, "full_name": "Malika", "phone": None, "is_verified": False},
        ])

    mock_outbound_http(monkeypatch, handler)
    profiles = await fetch_public_profiles([2, 1, 1])
    assert profiles[1].full_name == "Aziz"
    assert profiles[2].is_verified is False


async def test_fetch_public_profiles_skips_call_without_ids(monkeypatch):
    mock_outbound_http(monkeypatch, lambda request: (_ for _ in ()).throw(AssertionError("IAM must not be called")))
    assert await fetch_public_profiles([]) == {}


async def test_fetch_public_profiles_degrades_when_iam_fails(monkeypatch):
    mock_outbound_http(monkeypatch, lambda request: httpx.Response(503))
    assert await fetch_public_profiles([1]) == {}

    def unreachable(request):
        raise httpx.ConnectError("iam down")

    mock_outbound_http(monkeypatch, unreachable)
    assert await fetch_public_profiles([1]) == {}


async def test_fetch_public_profiles_ignores_malformed_payload(monkeypatch):
    mock_outbound_http(monkeypatch, lambda request: httpx.Response(200, json=[{"unexpected": True}]))
    assert await fetch_public_profiles([1]) == {}
