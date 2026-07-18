from datetime import datetime, timedelta, timezone

from jose import jwt
import bcrypt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_token(subject: str, expires_minutes: int, extra_claims: dict[str, object] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, object] = {"sub": subject, "iat": now, "exp": now + timedelta(minutes=expires_minutes)}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_otp_code(phone: str, otp: str) -> bool:
    """Validate an OTP code against the in-memory store (2-minute TTL, single-use)."""
    from app.utils.otp_store import verify_and_consume  # local import avoids circular deps
    return verify_and_consume(phone, otp)
