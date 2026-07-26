"""Users domain — SQLAlchemy ORM models.

Contains:
  - User, UserRole  (from app/models/user.py)
  - Notification, NotificationType (from app/models/notification.py)

RULE: This file MUST ONLY import from ``app.core.database`` (for Base).
      It must NEVER import from any other domain's models.py.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships — NOTE: Removed cross-domain string-based references for strict DB isolation
    # listings = relationship("Listing", back_populates="owner")
    # rentals = relationship("Rental", back_populates="student")
    # reviews = relationship("Review", back_populates="author")
    # subscriptions = relationship("Subscription", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------


class NotificationType(str, enum.Enum):
    rental_request = "rental_request"
    rental_accepted = "rental_accepted"
    rental_rejected = "rental_rejected"
    payment_due = "payment_due"
    maintenance = "maintenance"
    system = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    request_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="notifications")
