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


def create_token(subject: str, expires_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "iat": now, "exp": now + timedelta(minutes=expires_minutes)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# TODO: Replace with production SMS/TOTP verification backed by Redis or a dedicated OTP store.
DEV_OTP_CODE = "000000"


def verify_otp_code(_phone: str, otp: str) -> bool:
    """Validate an OTP code. Uses a hardcoded dev code until SMS integration is added."""
    return otp == DEV_OTP_CODE
