"""IAM Service — SQLAlchemy ORM models.

Mirrors the `users` table schema from the monolith (backend/app/domains/users/models.py).
Only the User model is needed here; notifications are out-of-scope for IAM.

RULE: Import ONLY from app.database (for Base). Never import from other services.
"""

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

    # Primary key IS the Telegram ID (BigInteger). Set by the caller — no autoincrement.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=False),
        nullable=False,
    )
    university: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} phone={self.phone} role={self.role}>"
