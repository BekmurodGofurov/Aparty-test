from collections.abc import AsyncGenerator
import ssl
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# Use PostgreSQL (Neon.tech for production, or local if available)
# Can set USE_SQLITE=true to use SQLite for local development
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"

if USE_SQLITE:
    # SQLite configuration for local development
    database_url = "sqlite+aiosqlite:///./aparty.db"
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL configuration for production
    database_url = settings.database_url
    connect_args = {}
    if "neon" in database_url:
        # Create SSL context for Neon.tech
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        connect_args = {"ssl": ssl_context}

engine = create_async_engine(
    database_url,
    echo=False,
    connect_args=connect_args
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
