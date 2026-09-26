"""IAM Service settings. Every value comes from the environment (or .env)."""

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

    database_url: str
    redis_url: str

    # JWT access tokens
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "aparty-iam"
    jwt_audience: str = "aparty-api"
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 10_080  # 7 days

    # Telegram login (OpenID Connect). Login is disabled until the client is configured.
    telegram_client_id: str | None = None
    telegram_client_secret: str | None = None
    telegram_redirect_uri: str | None = None
    telegram_scopes: str = "openid profile phone telegram:bot_access"
    telegram_auth_url: str = "https://oauth.telegram.org/auth"
    telegram_token_url: str = "https://oauth.telegram.org/token"
    telegram_jwks_url: str = "https://oauth.telegram.org/.well-known/jwks.json"
    telegram_issuer: str = "https://oauth.telegram.org"
    telegram_request_timeout_seconds: float = 5.0
    telegram_login_ttl_seconds: int = 600
    telegram_jwks_cache_seconds: int = 3600

    # Rate limits
    login_rate_limit_per_minute: int = 10
    admin_login_max_failures: int = 5
    admin_login_lockout_seconds: int = 900

    # Root admin
    admin_username: str
    admin_password: str

    cookie_secure: bool = False  # set COOKIE_SECURE=true behind HTTPS
    cors_origins: str

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_client_id and self.telegram_client_secret and self.telegram_redirect_uri)


settings = Settings()
