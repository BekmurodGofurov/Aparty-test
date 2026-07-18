from __future__ import annotations

import enum
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    owner = "owner"
    makler = "makler"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    # id IS the Telegram ID (BigInteger). Provided by the caller — no default.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    university: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    listings = relationship("Listing", back_populates="owner")
    rentals = relationship("Rental", back_populates="student")
    reviews = relationship("Review", back_populates="author")
    subscriptions = relationship("Subscription", back_populates="user")
