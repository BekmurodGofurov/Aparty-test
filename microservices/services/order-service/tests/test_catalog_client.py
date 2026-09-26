import uuid

import httpx
import pytest

from app.clients.catalog import CatalogUnavailableError, fetch_booking_info
from tests.helpers import mock_outbound_http

LISTING_ID = uuid.uuid4()


async def test_fetch_booking_info_returns_listing(monkeypatch):
    def handler(request):
        assert request.url.path == f"/api/v1/listings/{LISTING_ID}/booking-info"
        return httpx.Response(200, json={
            "id": str(LISTING_ID), "owner_id": 5, "price": 100.0, "status": "active", "is_active": True,
            "rental_type": "full_unit",
        })

    mock_outbound_http(monkeypatch, handler)
    info = await fetch_booking_info(LISTING_ID)
    assert (info.owner_id, info.price, info.status) == (5, 100.0, "active")
    assert info.parent_listing_id is None


async def test_fetch_booking_info_returns_none_for_missing_listing(monkeypatch):
    mock_outbound_http(monkeypatch, lambda request: httpx.Response(404))
    assert await fetch_booking_info(LISTING_ID) is None


@pytest.mark.parametrize("failure", ["server-error", "connection", "malformed"])
async def test_fetch_booking_info_reports_outages(monkeypatch, failure):
    def handler(request):
        if failure == "connection":
            raise httpx.ConnectError("catalog down")
        if failure == "malformed":
            return httpx.Response(200, json={"unexpected": True})
        return httpx.Response(500)

    mock_outbound_http(monkeypatch, handler)
    with pytest.raises(CatalogUnavailableError):
        await fetch_booking_info(LISTING_ID)
