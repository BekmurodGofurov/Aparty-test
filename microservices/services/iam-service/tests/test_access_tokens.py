from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.security import create_access_token, decode_access_token
from tests.conftest import TEST_JWT_SECRET


def forge(**overrides) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": "1", "type": "access", "role": "owner", "iss": "aparty-iam", "aud": "aparty-api",
              "iat": now, "exp": now + timedelta(minutes=5)}
    claims.update(overrides)
    return jwt.encode(claims, TEST_JWT_SECRET, algorithm="HS256")


def test_access_token_carries_issuer_audience_role_and_id():
    claims = decode_access_token(create_access_token(7, "owner"))
    assert (claims["sub"], claims["role"], claims["iss"], claims["aud"]) == ("7", "owner", "aparty-iam", "aparty-api")
    assert claims["jti"]


def test_role_is_null_until_chosen():
    assert decode_access_token(create_access_token(7, None))["role"] is None


@pytest.mark.parametrize(
    "token",
    [
        forge(aud="another-api"),
        forge(iss="another-issuer"),
        forge(type="refresh"),
        forge(exp=datetime.now(timezone.utc) - timedelta(minutes=1)),
    ],
    ids=["wrong-audience", "wrong-issuer", "wrong-type", "expired"],
)
def test_invalid_access_tokens_are_rejected(token):
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


async def test_endpoints_reject_invalid_tokens(client, create_user):
    await create_user(1)
    response = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {forge(aud='x')}"})
    assert response.status_code == 401
