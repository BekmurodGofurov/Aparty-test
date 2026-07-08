"""Unit tests for authentication and security utilities."""

from datetime import datetime, timezone

import pytest
from jose import jwt

from app.config import settings
from app.utils.security import (
    DEV_OTP_CODE,
    create_token,
    hash_password,
    verify_otp_code,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_returns_bcrypt_hash(self):
        hashed = hash_password("secret123")
        assert hashed.startswith("$2b$")
        assert len(hashed) > 20

    def test_verify_password_accepts_correct_password(self):
        password = "my-secure-password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_rejects_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_verify_password_rejects_invalid_hash(self):
        assert verify_password("password", "not-a-valid-hash") is False

    def test_verify_password_rejects_empty_password(self):
        hashed = hash_password("secret")
        assert verify_password("", hashed) is False


class TestOtpValidation:
    def test_verify_otp_accepts_dev_code(self):
        assert verify_otp_code("+998901234567", DEV_OTP_CODE) is True

    def test_verify_otp_rejects_invalid_code(self):
        assert verify_otp_code("+998901234567", "123456") is False

    def test_verify_otp_rejects_empty_code(self):
        assert verify_otp_code("+998901234567", "") is False


class TestJwtToken:
    def test_create_token_generates_valid_jwt(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_token(user_id, expires_minutes=30)
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload

    def test_create_token_expiry_is_in_future(self):
        user_id = "550e8400-e29b-41d4-a716-446655440001"
        token = create_token(user_id, expires_minutes=60)
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        assert exp > iat

    def test_create_token_different_subjects_produce_different_tokens(self):
        t1 = create_token("user-a", expires_minutes=30)
        t2 = create_token("user-b", expires_minutes=30)
        assert t1 != t2
