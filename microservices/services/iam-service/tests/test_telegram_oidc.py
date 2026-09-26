import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app import telegram_oidc
from app.telegram_oidc import TelegramAuthError, verify_id_token


def test_pkce_pair_matches_s256():
    import base64
    import hashlib

    verifier, challenge = telegram_oidc.new_pkce_pair()
    digest = hashlib.sha256(verifier.encode()).digest()
    assert challenge == base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    assert len(verifier) >= 43


def test_authorization_url_carries_pkce_and_scopes():
    from urllib.parse import parse_qs, urlsplit

    url = telegram_oidc.build_authorization_url("state-1", "challenge-1")
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    assert f"{parts.scheme}://{parts.netloc}{parts.path}" == "https://oauth.telegram.org/auth"
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"] == ["state-1"]
    assert query["response_type"] == ["code"]
    assert "phone" in query["scope"][0].split()


async def test_valid_token_returns_profile(telegram):
    profile = await verify_id_token(telegram.id_token())
    assert profile.telegram_id == 555001
    assert profile.full_name == "Aziz Karimov"
    assert profile.phone == "+998901234567"
    assert profile.username == "aziz"


async def test_name_is_built_from_given_and_family_name(telegram):
    token = telegram.id_token(name=None, given_name="Aziz", family_name="Karimov")
    assert (await verify_id_token(token)).full_name == "Aziz Karimov"


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "999"},
        {"iss": "https://evil.example"},
        {"exp": 1},
        {"phone_number": None},
        {"phone_number_verified": False},
        {"id": None, "sub": "not-a-number"},
    ],
    ids=["wrong-audience", "wrong-issuer", "expired", "no-phone", "unverified-phone", "bad-id"],
)
async def test_invalid_claims_are_rejected(telegram, overrides):
    with pytest.raises(TelegramAuthError):
        await verify_id_token(telegram.id_token(**overrides))


async def test_token_signed_with_another_key_is_rejected(telegram):
    forged = telegram.id_token(key=rsa.generate_private_key(public_exponent=65537, key_size=2048))
    with pytest.raises(TelegramAuthError):
        await verify_id_token(forged)


async def test_unknown_key_id_and_missing_key_id_are_rejected(telegram):
    with pytest.raises(TelegramAuthError):
        await verify_id_token(telegram.id_token(kid="other-key"))
    with pytest.raises(TelegramAuthError):
        await verify_id_token("not-a-jwt")


async def test_symmetric_algorithm_is_rejected(telegram):
    import jwt

    forged = jwt.encode(
        {"iss": "https://oauth.telegram.org", "aud": "123456", "sub": "1", "iat": 1, "exp": 9999999999,
         "phone_number": "998901234567"},
        "x" * 40, algorithm="HS256", headers={"kid": telegram.kid},
    )
    with pytest.raises(TelegramAuthError):
        await verify_id_token(forged)


async def test_signing_keys_are_cached(telegram):
    await verify_id_token(telegram.id_token())
    await verify_id_token(telegram.id_token())
    assert telegram.jwks_requests == 1
