from typing import Any, Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.models import User

from database.operations.select import users as select_users


async def update_fields(
    db: AsyncSession,
    user_id: int,
    **fields: Any,
) -> Optional[User]:
    if not fields:
        return await select_users.get_by_id(db, user_id)
    await db.execute(update(User).where(User.id == user_id).values(**fields))
    await db.commit()
    return await select_users.get_by_id(db, user_id)


async def set_verified(db: AsyncSession, user_id: int, *, is_verified: bool) -> Optional[User]:
    return await update_fields(db, user_id, is_verified=is_verified)


async def verify_user(db: AsyncSession, user_id: int) -> Optional[User]:
    return await set_verified(db, user_id, is_verified=True)

