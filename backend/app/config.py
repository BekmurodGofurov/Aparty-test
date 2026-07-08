from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql+asyncpg://neondb_owner:npg_dUgfK9jbG2wL@ep-rapid-silence-aml9hxip-pooler.c-5.us-east-1.aws.neon.tech/neondb"
    sync_database_url: str = "postgresql+psycopg://neondb_owner:npg_dUgfK9jbG2wL@ep-rapid-silence-aml9hxip-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    jwt_secret_key: str = "aparty-secret-key-2024-super-secure"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    db_connect_timeout_seconds: int = 5
    auto_migrate_on_startup: bool = True
    cookie_secure: bool = False
    groq_api_key: str = ""
    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:5173,"
        "http://localhost:5174,"
        "http://localhost:5175,"
        "http://localhost:5176,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:5174,"
        "http://127.0.0.1:5175,"
        "http://127.0.0.1:5176,"
        "https://one-one-ezd.pages.dev,"
        "https://aparty.uz,"
        "https://www.aparty.uz"
    )


settings = Settings()
