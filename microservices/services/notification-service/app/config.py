"""Notification Service settings. Every value comes from the environment (or .env)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SERVICE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "notification-service"
    database_url: str
    rabbitmq_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "aparty-iam"
    jwt_audience: str = "aparty-api"
    iam_service_url: str
    iam_request_timeout_seconds: float = 3.0
    bot_token: str | None = None
    telegram_api_url: str = "https://api.telegram.org"
    telegram_request_timeout_seconds: float = 5.0
    site_url: str | None = None
    cors_origins: str
    default_page_size: int = 30
    max_page_size: int = 100

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
