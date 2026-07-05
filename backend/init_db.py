#!/usr/bin/env python3
"""Initialize database schema."""
import asyncio
from app.config import settings
from app.database import Base, engine
from app.models import listing, listing_payment, payment, rental, review, subscription, user, favorite  # noqa: F401


async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
