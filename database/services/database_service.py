from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal


class DatabaseService:
    """Thin async session wrapper for scripts and background tasks."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def close(self) -> None:
        await self.session.close()


@asynccontextmanager
async def get_database_service() -> AsyncGenerator[DatabaseService, None]:
    """Context manager for database service."""
    async with AsyncSessionLocal() as session:
        db_service = DatabaseService(session)
        try:
            yield db_service
            await db_service.commit()
        except Exception:
            await db_service.rollback()
            raise
