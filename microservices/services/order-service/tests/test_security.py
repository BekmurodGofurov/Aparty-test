from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import auth_headers, make_token

ENDPOINT = "/api/v1/bookings"


async def test_missing_token_is_rejected(client):
    assert (await client.get(ENDPOINT)).status_code == 401


async def test_valid_token_is_accepted(client):
    assert (await client.get(ENDPOINT, headers=auth_headers(1))).status_code == 200


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
    assert (await client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})).status_code == 401
