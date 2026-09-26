from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import auth_headers, make_token

ENDPOINT = "/api/v1/listings/me"


async def test_missing_token_is_rejected(client):
    assert (await client.get(ENDPOINT)).status_code == 401


async def test_valid_token_is_accepted(client):
    assert (await client.get(ENDPOINT, headers=auth_headers(7))).status_code == 200


@pytest.mark.parametrize(
    "token",
    [
        make_token(1, secret="another-secret-that-is-long-enough-32b"),
        make_token(1, token_type="refresh"),
        make_token("admin"),
        make_token(1, aud="another-api"),
        make_token(1, iss="another-issuer"),
        make_token(1, exp=datetime.now(timezone.utc) - timedelta(minutes=1)),
        "not-a-jwt",
    ],
    ids=["wrong-secret", "refresh-token", "non-numeric-subject", "wrong-audience", "wrong-issuer", "expired", "garbage"],
)
async def test_invalid_tokens_are_rejected(client, token):
    response = await client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_user_id_header_cannot_impersonate(client):
    response = await client.get(ENDPOINT, headers={"X-User-ID": "1"})
    assert response.status_code == 401
