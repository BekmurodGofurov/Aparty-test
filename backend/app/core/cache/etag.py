"""ETag (Entity Tag) support for FastAPI endpoints.

Provides a ``@etag`` decorator that:

1. Computes a SHA-256 hash of the serialised JSON response body.
2. Injects it as the ``ETag`` response header (weak ETag: ``W/"<hash>"``).
3. Checks the incoming ``If-None-Match`` request header.  If the client-sent
   ETag matches the computed one, immediately returns **304 Not Modified**
   with an empty body — saving bandwidth and achieving zero-latency on the
   client when data hasn't changed.

The decorator is designed to compose cleanly with ``@cached()`` — place
``@etag`` **above** ``@cached()`` so that the ETag check runs first on the
already-cached response body.

Usage::

    @router.get("/items")
    @etag
    @cached(key_template="aparty:items:all", ttl=300)
    async def list_items(request: Request, ...):
        ...

Why SHA-256 over MD5?
    SHA-256 is not used here for *security* — ETags are not secrets — but
    because SHA-256 has zero risk of accidental collisions on response bodies
    of any realistic size, and its performance difference vs MD5 is negligible
    for the payload sizes we serve (< 1 MB).
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
from typing import Any, Callable, TypeVar

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def _compute_etag(body_bytes: bytes) -> str:
    """Compute a weak ETag from raw response bytes."""
    digest = hashlib.sha256(body_bytes).hexdigest()
    return f'W/"{digest}"'


def _etags_match(client_etag: str, server_etag: str) -> bool:
    """Weak ETag comparison per RFC 7232 §2.3.2."""
    if not client_etag:
        return False
    if client_etag.strip() == "*":
        return True

    client_tags = [tag.strip() for tag in client_etag.split(",")]

    def _opaque(tag: str) -> str:
        tag = tag.strip()
        if tag.startswith("W/"):
            tag = tag[2:]
        return tag.strip('"')

    server_opaque = _opaque(server_etag)
    return any(_opaque(tag) == server_opaque for tag in client_tags)


def etag(func: F) -> F:
    """Decorator that adds ETag / ``If-None-Match`` (304) support."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        request: Request | None = kwargs.get("request")
        if request is None:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

        if request is None:
            return await func(*args, **kwargs)

        result = await func(*args, **kwargs)

        if isinstance(result, JSONResponse):
            body_bytes: bytes = result.body
            existing_headers: dict = dict(result.headers)
        elif isinstance(result, Response):
            body_bytes = result.body
            existing_headers = dict(result.headers)
        elif isinstance(result, BaseModel):
            body_bytes = result.model_dump_json().encode("utf-8")
            existing_headers = {}
        elif isinstance(result, (dict, list)):
            body_bytes = json.dumps(result, separators=(",", ":"), sort_keys=True).encode("utf-8")
            existing_headers = {}
        else:
            return result

        server_etag = _compute_etag(body_bytes)
        client_etag = request.headers.get("if-none-match", "")

        if _etags_match(client_etag, server_etag):
            return Response(
                status_code=304,
                headers={
                    "ETag": server_etag,
                    **{k: v for k, v in existing_headers.items()
                       if k.lower() in ("x-cache", "cache-control")},
                },
            )

        response_headers = {**existing_headers, "ETag": server_etag}

        if isinstance(result, (JSONResponse, Response)):
            return JSONResponse(
                content=json.loads(body_bytes),
                status_code=result.status_code,
                headers=response_headers,
            )

        return JSONResponse(
            content=json.loads(body_bytes) if isinstance(body_bytes, bytes) else result,
            headers=response_headers,
        )

    return wrapper  # type: ignore[return-value]
