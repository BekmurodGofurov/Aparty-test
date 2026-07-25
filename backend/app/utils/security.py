from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings




def create_token(subject: str, expires_minutes: int, extra_claims: dict[str, object] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, object] = {"sub": subject, "iat": now, "exp": now + timedelta(minutes=expires_minutes)}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
