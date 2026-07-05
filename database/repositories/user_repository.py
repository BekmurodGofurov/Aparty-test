import uuid
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Role
from database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """User database operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram/user ID."""
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number"""
        result = await self.session.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users by role"""
        result = await self.session.execute(
            select(User).join(Role, User.role_id == Role.id).where(Role.name == role).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_verified_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all verified users"""
        result = await self.session.execute(
            select(User).where(User.verified == True).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def verify_user(self, user_id: int) -> Optional[User]:
        """Mark user as verified"""
        return await self.update(user_id, verified=True)

    async def update_password(self, user_id: int, password_hash: str) -> Optional[User]:
        """Update user password"""
        return await self.update(user_id, password_hash=password_hash)
