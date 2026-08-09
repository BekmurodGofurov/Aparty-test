"""IAM Service — Configuration.

All settings are loaded from environment variables (or a .env file).
Defaults are provided only for non-sensitive, local-development values.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

IAM_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=IAM_DIR.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str  # must be set via env (e.g. Neon DB asyncpg URL)

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret_key: str  # must be set via env
    jwt_algorithm: str = "HS256"

    # ── Token expiry ──────────────────────────────────────────────────────────
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 10_080  # 7 days

    # ── OTP ───────────────────────────────────────────────────────────────────
    otp_ttl_seconds: int = 120

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
