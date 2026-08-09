"""IAM Service — SQLAlchemy async database connection (Neon DB / PostgreSQL)."""

import ssl

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import settings

# SSL context required by Neon DB
_ssl_ctx = ssl.create_default_context()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "ssl": _ssl_ctx,
        "timeout": 10,
    },
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """FastAPI dependency: yield an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables that don't yet exist.

    NOTE: For production, use Alembic migrations instead.
    This is only used for local dev / first-time setup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
