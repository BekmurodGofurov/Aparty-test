"""Catalog Service Settings configuration."""

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

    database_url: str
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    jwt_secret_key: str = "aparty-secret-key-2024-super-secure"
    jwt_algorithm: str = "HS256"
    service_name: str = "catalog-service"


settings = Settings()
