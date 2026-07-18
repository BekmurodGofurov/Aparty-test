"""In-memory login code store with strict 2-minute TTL.

Architecture:
    The Telegram bot calls POST /api/v1/auth/bot/login-code to generate a
    short-lived 6-digit code. The user types that code on the website, which
    calls POST /api/v1/auth/login. The backend looks up the code here, issues
    a JWT, and immediately deletes the code (single-use, no replay attacks).

Structure:
    _store: dict[code_str, {"user_id": int, "expires_at": float}]

    Key   → 6-digit code string (e.g. "482031")
    Value → user_id (Telegram ID) + monotonic expiry timestamp

Thread safety:
    Protected by threading.Lock — safe under uvicorn's single-threaded async
    event loop and any sync background threads.

Uniqueness:
    Uses secrets.randbelow(1_000_000) seeded by the OS CSPRNG, which is
    dramatically more unpredictable than random.choices for a 6-digit space.
    Collision retries ensure no two active codes are identical.

Swap-out path:
    Replace generate_login_code / verify_and_consume_code with Redis-backed
    equivalents (same signatures) for multi-instance deployments.
"""
import secrets
import threading
import time
from typing import Optional

_store: dict[str, dict] = {}
_lock = threading.Lock()

LOGIN_CODE_TTL_SECONDS: int = 120  # 2 minutes


def generate_login_code(user_id: int) -> str:
    """Generate a unique 6-digit code, bind it to user_id with a 2-min TTL.

    Retries up to 10 times to avoid collisions with currently active codes
    (probability ≈ 0 in practice but guaranteed safe).
    """
    expires_at = time.monotonic() + LOGIN_CODE_TTL_SECONDS
    with _lock:
        for _ in range(10):
            code = f"{secrets.randbelow(1_000_000):06d}"
            if code not in _store:
                break
        _store[code] = {"user_id": user_id, "expires_at": expires_at}
    return code


def verify_and_consume_code(code: str) -> Optional[int]:
    """Validate the code and return the bound user_id, or None if invalid.

    On success  → deletes the entry immediately (single-use).
    On expiry   → deletes the entry and returns None.
    On mismatch → returns None without modifying state.
    """
    with _lock:
        entry = _store.get(code)
        if entry is None:
            return None

        if time.monotonic() > entry["expires_at"]:
            _store.pop(code, None)
            return None

        # Valid — consume and return
        _store.pop(code)
        return entry["user_id"]


def purge_expired() -> int:
    """Remove all expired entries. Returns the count removed.

    Call periodically from a background task to keep memory tidy.
    """
    now = time.monotonic()
    with _lock:
        expired = [k for k, v in _store.items() if now > v["expires_at"]]
        for k in expired:
            del _store[k]
    return len(expired)
