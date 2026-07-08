import uuid
from typing import Any, Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

from database.operations.select import users as select_users


async def update_fields(
    db: AsyncSession,
    user_id: uuid.UUID,
    **fields: Any,
) -> Optional[User]:
    if not fields:
        return await select_users.get_by_id(db, user_id)
    await db.execute(update(User).where(User.id == user_id).values(**fields))
    await db.commit()
    return await select_users.get_by_id(db, user_id)


async def set_verified(db: AsyncSession, user_id: uuid.UUID, *, is_verified: bool) -> Optional[User]:
    return await update_fields(db, user_id, is_verified=is_verified)


async def verify_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    return await set_verified(db, user_id, is_verified=True)


async def update_password(
    db: AsyncSession,
    user_id: uuid.UUID,
    password_hash: str,
) -> Optional[User]:
    return await update_fields(db, user_id, hashed_password=password_hash)
