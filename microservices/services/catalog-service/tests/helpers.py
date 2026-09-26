import httpx

REAL_ASYNC_CLIENT = httpx.AsyncClient


def mock_outbound_http(monkeypatch, handler):
    """Route every httpx.AsyncClient created by the app through `handler`."""
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: REAL_ASYNC_CLIENT(transport=httpx.MockTransport(handler), **kwargs),
    )
