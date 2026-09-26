"""Telegram Login (OpenID Connect, authorization code flow with PKCE)."""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
import time
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

# EdDSA and ES256K tokens cannot carry the profile and phone claims, so they are not accepted.
ALLOWED_ALGORITHMS = ["RS256", "ES256"]
REQUIRED_CLAIMS = ["exp", "iat", "iss", "aud", "sub"]

_jwks_cache: dict = {"keys": {}, "fetched_at": 0.0}


class TelegramAuthError(Exception):
    """Login with Telegram failed. The message is safe to show to the client."""


class TelegramProfile(BaseModel):
    telegram_id: int
    full_name: str
    username: Optional[str] = None
    picture: Optional[str] = None
    phone: str


def new_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for the S256 method."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def build_authorization_url(state: str, code_challenge: str) -> str:
    query = urlencode(
        {
            "client_id": settings.telegram_client_id,
            "redirect_uri": settings.telegram_redirect_uri,
            "response_type": "code",
            "scope": settings.telegram_scopes,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{settings.telegram_auth_url}?{query}"


async def exchange_code(code: str, code_verifier: str) -> str:
    """Exchange the authorization code for an id_token on the server side."""
    try:
        async with httpx.AsyncClient(timeout=settings.telegram_request_timeout_seconds) as client:
            response = await client.post(
                settings.telegram_token_url,
                auth=(settings.telegram_client_id, settings.telegram_client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.telegram_redirect_uri,
                    "client_id": settings.telegram_client_id,
                    "code_verifier": code_verifier,
                },
            )
        response.raise_for_status()
        return response.json()["id_token"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("Telegram token exchange failed: %s", exc)
        raise TelegramAuthError("Telegram rejected the login. Please try again.") from exc


async def _fetch_jwks() -> dict:
    try:
        async with httpx.AsyncClient(timeout=settings.telegram_request_timeout_seconds) as client:
            response = await client.get(settings.telegram_jwks_url)
        response.raise_for_status()
        return {key["kid"]: key for key in response.json()["keys"]}
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.error("Could not load Telegram signing keys: %s", exc)
        raise TelegramAuthError("Could not verify the Telegram login. Please try again.") from exc


async def _signing_key(kid: str) -> jwt.PyJWK:
    """Look up a signing key, refreshing the cache when it is stale or the key is unknown."""
    cache_age = time.monotonic() - _jwks_cache["fetched_at"]
    if kid not in _jwks_cache["keys"] or cache_age > settings.telegram_jwks_cache_seconds:
        _jwks_cache["keys"] = await _fetch_jwks()
        _jwks_cache["fetched_at"] = time.monotonic()
    if kid not in _jwks_cache["keys"]:
        raise TelegramAuthError("Invalid Telegram login token.")
    return jwt.PyJWK(_jwks_cache["keys"][kid])


def _normalize_phone(raw: str) -> str:
    digits = "".join(char for char in raw if char.isdigit())
    return f"+{digits}"


async def verify_id_token(id_token: str) -> TelegramProfile:
    """Validate the id_token signature and claims and return the Telegram profile."""
    try:
        kid = jwt.get_unverified_header(id_token).get("kid")
        if not kid:
            raise TelegramAuthError("Invalid Telegram login token.")
        key = await _signing_key(kid)
        claims = jwt.decode(
            id_token,
            key.key,
            algorithms=ALLOWED_ALGORITHMS,
            audience=settings.telegram_client_id,
            issuer=settings.telegram_issuer,
            options={"require": REQUIRED_CLAIMS},
        )
    except jwt.InvalidTokenError as exc:
        raise TelegramAuthError("Invalid Telegram login token.") from exc

    phone = claims.get("phone_number")
    if not phone or claims.get("phone_number_verified") is False:
        raise TelegramAuthError("A verified phone number is required. Please allow phone access and try again.")

    try:
        telegram_id = int(claims.get("id") or claims["sub"])
    except (KeyError, ValueError) as exc:
        raise TelegramAuthError("Invalid Telegram login token.") from exc

    name = claims.get("name") or " ".join(
        part for part in (claims.get("given_name"), claims.get("family_name")) if part
    )
    return TelegramProfile(
        telegram_id=telegram_id,
        full_name=(name or "Telegram user")[:100],
        username=claims.get("preferred_username"),
        picture=claims.get("picture"),
        phone=_normalize_phone(phone),
    )
