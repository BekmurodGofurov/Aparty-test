"""In-memory OTP store with a strict 2-minute TTL.

Structure:
    _store: dict[phone_str, (otp_code_str, expires_at_float)]

Thread safety: protected by a threading.Lock so it remains safe
under uvicorn's default single-threaded async event loop as well as
any sync background threads.

Swap-out path: replace `generate_and_store` and `verify_and_consume`
with Redis-backed equivalents (same signatures) for multi-instance deployments.
"""
import random
import string
import threading
import time

_store: dict[str, tuple[str, float]] = {}
_lock = threading.Lock()

OTP_TTL_SECONDS: int = 120  # 2 minutes


def generate_and_store(phone: str) -> str:
    """Generate a 6-digit OTP, store it with a 2-minute TTL and return it."""
    otp = "".join(random.choices(string.digits, k=6))
    expires_at = time.monotonic() + OTP_TTL_SECONDS
    with _lock:
        _store[phone] = (otp, expires_at)
    return otp


def verify_and_consume(phone: str, code: str) -> bool:
    """
    Return True if the code matches and has not expired.

    On a successful match the entry is deleted immediately (single-use).
    On an expired entry the entry is also deleted (cleanup).
    Returns False for any invalid/expired/missing case.
    """
    with _lock:
        entry = _store.get(phone)
        if entry is None:
            return False

        stored_code, expires_at = entry

        if time.monotonic() > expires_at:
            # Expired — remove and reject
            _store.pop(phone, None)
            return False

        if stored_code != code:
            return False

        # Valid match — consume (one-time use)
        _store.pop(phone, None)
        return True


def purge_expired() -> int:
    """Remove all expired entries. Returns the number of entries removed.

    Call periodically (e.g. from a background task) to keep memory tidy.
    """
    now = time.monotonic()
    with _lock:
        expired_keys = [k for k, (_, exp) in _store.items() if now > exp]
        for k in expired_keys:
            del _store[k]
    return len(expired_keys)
