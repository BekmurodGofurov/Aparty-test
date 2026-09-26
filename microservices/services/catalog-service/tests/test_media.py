import httpx
import pytest

from app.config import settings
from tests.conftest import auth_headers
from tests.helpers import mock_outbound_http

UPLOAD = "/api/v1/media/upload"


def image_file(name="photo.png", content=b"fake-image-bytes", content_type="image/png"):
    return {"file": (name, content, content_type)}


@pytest.fixture
def imgbb_key(monkeypatch):
    monkeypatch.setattr(settings, "imgbb_api_key", "test-key")


async def test_upload_requires_auth(client):
    assert (await client.post(UPLOAD, files=image_file())).status_code == 401


async def test_upload_rejects_unsupported_extension(client):
    response = await client.post(UPLOAD, files=image_file("movie.mp4", content_type="video/mp4"), headers=auth_headers(1))
    assert response.status_code == 400


async def test_upload_rejects_wrong_content_type(client):
    response = await client.post(UPLOAD, files=image_file(content_type="text/plain"), headers=auth_headers(1))
    assert response.status_code == 400


async def test_upload_rejects_oversized_file(client, monkeypatch, imgbb_key):
    monkeypatch.setattr(settings, "max_upload_size_bytes", 10)
    response = await client.post(UPLOAD, files=image_file(content=b"x" * 11), headers=auth_headers(1))
    assert response.status_code == 413


async def test_upload_without_api_key_is_unavailable(client, monkeypatch):
    monkeypatch.setattr(settings, "imgbb_api_key", None)
    assert (await client.post(UPLOAD, files=image_file(), headers=auth_headers(1))).status_code == 503


async def test_upload_success_returns_urls(client, monkeypatch, imgbb_key):
    def handler(request):
        assert request.url.params["key"] == "test-key"
        return httpx.Response(200, json={"success": True, "data": {"display_url": "https://i.test/a.png", "delete_url": "https://i.test/del"}})

    mock_outbound_http(monkeypatch, handler)
    for path in (UPLOAD, "/api/v1/media/image"):
        response = await client.post(path, files=image_file(), headers=auth_headers(1))
        assert response.status_code == 201
        assert response.json()["display_url"] == "https://i.test/a.png"
        assert response.json()["url"] == "https://i.test/a.png"
        assert response.json()["delete_url"] == "https://i.test/del"


async def test_upload_maps_provider_failure_to_502(client, monkeypatch, imgbb_key):
    mock_outbound_http(monkeypatch, lambda request: httpx.Response(500, text="boom"))
    assert (await client.post(UPLOAD, files=image_file(), headers=auth_headers(1))).status_code == 502

    mock_outbound_http(monkeypatch, lambda request: httpx.Response(200, json={"success": False}))
    assert (await client.post(UPLOAD, files=image_file(), headers=auth_headers(1))).status_code == 502
