from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Look up a user by their Telegram ID (which is the primary key)."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_all(db: AsyncSession, *, order_by_created_desc: bool = True) -> list[User]:
    query = select(User)
    if order_by_created_desc:
        query = query.order_by(User.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_by_role(
    db: AsyncSession,
    role: UserRole,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    result = await db.execute(
        select(User).where(User.role == role).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_verified_users(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    result = await db.execute(
        select(User).where(User.is_verified.is_(True)).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def count_all(db: AsyncSession) -> int:
    return (await db.execute(select(func.count(User.id)))).scalar_one()


async def count_verified(db: AsyncSession) -> int:
    return (
        await db.execute(select(func.count(User.id)).where(User.is_verified.is_(True)))
    ).scalar_one()


async def count_by_role(db: AsyncSession) -> list[tuple[UserRole | None, int]]:
    result = await db.execute(select(User.role, func.count(User.id)).group_by(User.role))
    return list(result.all())
