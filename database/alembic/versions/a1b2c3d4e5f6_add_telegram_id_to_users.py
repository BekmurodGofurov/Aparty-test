"""add telegram_id to users

Revision ID: a1b2c3d4e5f6
Revises: 68cd46c03a9d
Create Date: 2026-07-16 07:22:00.000000

Adds a nullable, unique, indexed BigInteger column `telegram_id` to the
`users` table. This links each user to their Telegram account so the
FastAPI backend can deliver OTP codes directly via the Bot API.

Safety guarantees:
- NULLABLE: existing rows are unaffected (no backfill required).
- UNIQUE constraint: one Telegram account cannot be shared across users.
- INDEX: the /bot/check/{telegram_id} lookup is O(log n).
- downgrade() fully reverses the change with zero data loss.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "68cd46c03a9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the column — nullable so every existing row keeps NULL.
    op.add_column(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
    )

    # 2. Unique constraint — prevents two accounts sharing one Telegram ID.
    #    Named explicitly so downgrade() can drop it by name on any DB engine.
    op.create_unique_constraint(
        "uq_users_telegram_id",
        "users",
        ["telegram_id"],
    )

    # 3. Index — makes GET /bot/check/{telegram_id} fast at any table size.
    op.create_index(
        op.f("ix_users_telegram_id"),
        "users",
        ["telegram_id"],
        unique=False,  # uniqueness is enforced by the constraint above
    )


def downgrade() -> None:
    # Reverse in strict dependency order: index → constraint → column.
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_constraint("uq_users_telegram_id", "users", type_="unique")
    op.drop_column("users", "telegram_id")
