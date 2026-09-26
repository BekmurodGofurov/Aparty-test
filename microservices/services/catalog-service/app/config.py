"""Catalog Service settings. Every value comes from the environment (or .env)."""

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

    service_name: str = "catalog-service"
    database_url: str
    rabbitmq_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "aparty-iam"
    jwt_audience: str = "aparty-api"
    iam_service_url: str
    iam_request_timeout_seconds: float = 3.0
    imgbb_api_key: str | None = None
    imgbb_upload_url: str = "https://api.imgbb.com/1/upload"
    max_upload_size_bytes: int = 5 * 1024 * 1024
    cors_origins: str
    premium_duration_days: int = 30
    roommate_listing_days: int = 30

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
