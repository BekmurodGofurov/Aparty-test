import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from tests.conftest import auth_headers
from app.domains.users.models import User

pytestmark = pytest.mark.asyncio

MOCK_IMGBB_URL = "https://i.ibb.co/example.jpg"

@pytest.fixture
def mock_httpx_client():
    with patch("app.routers.upload.httpx.AsyncClient") as mock_client_cls:
        # Create an instance mock
        mock_client_instance = mock_client_cls.return_value
        
        # Async context manager mock: __aenter__ returns the instance itself
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        
        # The post method returns a response
        from unittest.mock import MagicMock
        mock_post_response = AsyncMock()
        mock_post_response.status_code = 200
        mock_post_response.json = MagicMock(return_value={
            "success": True,
            "data": {"url": MOCK_IMGBB_URL}
        })
        
        mock_client_instance.post = AsyncMock(return_value=mock_post_response)
        yield mock_client_instance.post

class TestUploads:
    @pytest.mark.parametrize("filename", [
        "test.jpg", "test.jpeg", "test.png", "test.webp",
        "test.svg", "test.exe", "test.sh", "test.pdf", "test.txt",
        "", "test", "a"*1000 + ".jpg", "<script>.jpg"
    ])
    @pytest.mark.parametrize("content_type", [
        "image/jpeg", "image/png", "image/webp",
        "image/svg+xml", "application/pdf", "text/plain",
        "application/x-sh", "application/octet-stream", ""
    ])
    async def test_mimetype_enforcement(self, client: AsyncClient, makler_user: User, mock_httpx_client, filename, content_type):
        headers = auth_headers(makler_user)
        files = {"file": (filename, b"dummy content", content_type)}
    
        resp = await client.post("/api/v1/upload/image", files=files, headers=headers)
        
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        valid_ext = ext in ["jpg", "jpeg", "png", "webp"]
        valid_content_type = content_type in ["image/jpeg", "image/png", "image/webp"]
        valid_filename = bool(filename)
        
        if valid_ext and valid_content_type and valid_filename:
            assert resp.status_code == 201
            assert resp.json()["url"] == MOCK_IMGBB_URL
            mock_httpx_client.assert_called_once()
        else:
            assert resp.status_code in [400, 422]
            mock_httpx_client.assert_not_called()

    @pytest.mark.parametrize("size_bytes, expected_status", [
        (1024, 201), # 1KB
        (5 * 1024 * 1024, 201), # 5MB limit exact
        ((5 * 1024 * 1024) + 1, 413), # 1 byte over limit
        (6 * 1024 * 1024, 413), # 6MB
    ])
    async def test_file_size_limit_enforced(self, client: AsyncClient, makler_user: User, mock_httpx_client, size_bytes, expected_status):
        headers = auth_headers(makler_user)
        
        large_content = b"a" * size_bytes
        files = {"file": ("test.jpg", large_content, "image/jpeg")}
        
        resp = await client.post("/api/v1/upload/image", files=files, headers=headers)
        assert resp.status_code == expected_status
        if expected_status == 413:
            assert "hajmi" in resp.json()["detail"].lower() or "too large" in resp.json()["detail"].lower()

    async def test_unauthorized_upload(self, client: AsyncClient):
        files = {"file": ("test.jpg", b"dummy content", "image/jpeg")}
        resp = await client.post("/api/v1/upload/image", files=files)
        assert resp.status_code == 401
