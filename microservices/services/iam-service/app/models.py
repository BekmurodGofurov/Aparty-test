"""IAM Service ORM models."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    owner = "owner"
    makler = "makler"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    # Primary key is the Telegram user id.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    # None until the user picks a role after the first Telegram login.
    role: Mapped[Optional[UserRole]] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=False),
        nullable=True,
    )
    telegram_username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    university: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} phone={self.phone} role={self.role}>"
