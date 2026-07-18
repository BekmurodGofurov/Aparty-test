"""Use Telegram ID as users.id primary key (UUID → BigInteger).

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-16

## What this migration does

Replaces the UUID primary key on `users` with a BigInteger that stores the
Telegram user ID directly.  The `telegram_id` column (added in revision
a1b2c3d4e5f6) is dropped — it is now redundant because id IS the Telegram ID.
`hashed_password` is made nullable to support bot-registered users.

## Why dropping all foreign keys first

PostgreSQL will not let you ALTER the type of a column that is referenced by
a foreign key constraint.  We therefore:

  1. Drop every FK constraint that points at users.id.
  2. Change users.id from UUID to BIGINT.
  3. Change every referencing column from UUID to BIGINT.
  4. Re-add the FK constraints.

## Data safety

Existing UUID rows CANNOT be cast to BigInteger — the types are incompatible.
The migration TRUNCATES the users table (and all dependent tables, via
CASCADE) before altering the column.  This is safe for a development database
where the only real users are test accounts.

If you have production data, run a manual export first, truncate, migrate,
then re-import with Telegram IDs as the new IDs.

## Tables affected

Primary key:
  users.id   UUID → BIGINT

Foreign-key columns referencing users.id:
  listings.owner_id
  rentals.student_id
  rental_requests.requester_id, recipient_id
  rental_request_messages.sender_id
  room_messages.sender_id
  maintenance_reports.reporter_id, recipient_id
  payments.payer_id
  reviews.author_id
  subscriptions.user_id
  listing_payments.user_id
  favorites.user_id
  notifications.user_id, actor_id

Removed:
  users.telegram_id column + its unique constraint + index

Modified:
  users.hashed_password  NOT NULL → NULL
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Helpers: FK constraint names as they were created in the initial migration
# ---------------------------------------------------------------------------

# (table, constraint_name, fk_column, referenced_table)
_USER_FK_CONSTRAINTS = [
    # listings
    ("listings", "listings_owner_id_fkey", "owner_id", "users"),
    # rentals
    ("rentals", "rentals_student_id_fkey", "student_id", "users"),
    # rental_requests
    ("rental_requests", "rental_requests_requester_id_fkey", "requester_id", "users"),
    ("rental_requests", "rental_requests_recipient_id_fkey", "recipient_id", "users"),
    # rental_request_messages
    ("rental_request_messages", "rental_request_messages_sender_id_fkey", "sender_id", "users"),
    # room_messages
    ("room_messages", "room_messages_sender_id_fkey", "sender_id", "users"),
    # maintenance_reports
    ("maintenance_reports", "maintenance_reports_reporter_id_fkey", "reporter_id", "users"),
    ("maintenance_reports", "maintenance_reports_recipient_id_fkey", "recipient_id", "users"),
    # payments
    ("payments", "payments_payer_id_fkey", "payer_id", "users"),
    # reviews
    ("reviews", "reviews_author_id_fkey", "author_id", "users"),
    # subscriptions
    ("subscriptions", "subscriptions_user_id_fkey", "user_id", "users"),
    # listing_payments
    ("listing_payments", "listing_payments_user_id_fkey", "user_id", "users"),
    # favorites
    ("favorites", "favorites_user_id_fkey", "user_id", "users"),
    # notifications
    ("notifications", "notifications_user_id_fkey", "user_id", "users"),
    ("notifications", "notifications_actor_id_fkey", "actor_id", "users"),
]

# Columns that are nullable (payer_id, actor_id) need special handling
_NULLABLE_FK_COLS = {"payments.payer_id", "notifications.actor_id"}


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 0. Truncate all dependent tables to clear UUID data that cannot
    #    be cast to BIGINT.  CASCADE handles FK order automatically.
    # ------------------------------------------------------------------
    op.execute("TRUNCATE TABLE notifications CASCADE")
    op.execute("TRUNCATE TABLE favorites CASCADE")
    op.execute("TRUNCATE TABLE listing_payments CASCADE")
    op.execute("TRUNCATE TABLE subscriptions CASCADE")
    op.execute("TRUNCATE TABLE reviews CASCADE")
    op.execute("TRUNCATE TABLE payments CASCADE")
    op.execute("TRUNCATE TABLE maintenance_reports CASCADE")
    op.execute("TRUNCATE TABLE room_messages CASCADE")
    op.execute("TRUNCATE TABLE rental_request_messages CASCADE")
    op.execute("TRUNCATE TABLE rental_requests CASCADE")
    op.execute("TRUNCATE TABLE rentals CASCADE")
    op.execute("TRUNCATE TABLE listings CASCADE")
    op.execute("TRUNCATE TABLE users CASCADE")

    # ------------------------------------------------------------------
    # 1. Drop all FK constraints that reference users.id
    # ------------------------------------------------------------------
    for table, constraint, col, ref in _USER_FK_CONSTRAINTS:
        op.drop_constraint(constraint, table, type_="foreignkey")

    # ------------------------------------------------------------------
    # 2. Drop the telegram_id column (and its unique constraint + index)
    #    added in the previous migration (a1b2c3d4e5f6).
    # ------------------------------------------------------------------
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_constraint("uq_users_telegram_id", "users", type_="unique")
    op.drop_column("users", "telegram_id")

    # ------------------------------------------------------------------
    # 3. Alter users.id from UUID to BIGINT
    #    (USING clause is required by PostgreSQL for type conversion)
    # ------------------------------------------------------------------
    op.execute(
        "ALTER TABLE users ALTER COLUMN id TYPE BIGINT USING 0"
        # After truncation the table is empty — the USING expression is
        # never actually evaluated, but PostgreSQL still requires it.
    )

    # ------------------------------------------------------------------
    # 4. Alter every FK column from UUID to BIGINT
    # ------------------------------------------------------------------
    fk_col_changes = [
        # (table, column, nullable)
        ("listings", "owner_id", False),
        ("rentals", "student_id", False),
        ("rental_requests", "requester_id", False),
        ("rental_requests", "recipient_id", False),
        ("rental_request_messages", "sender_id", False),
        ("room_messages", "sender_id", False),
        ("maintenance_reports", "reporter_id", False),
        ("maintenance_reports", "recipient_id", False),
        ("payments", "payer_id", True),     # nullable
        ("reviews", "author_id", False),
        ("subscriptions", "user_id", False),
        ("listing_payments", "user_id", False),
        ("favorites", "user_id", False),
        ("notifications", "user_id", False),
        ("notifications", "actor_id", True),  # nullable
    ]
    for table, col, nullable in fk_col_changes:
        op.alter_column(
            table,
            col,
            existing_type=postgresql.UUID(as_uuid=True),
            type_=sa.BigInteger(),
            existing_nullable=nullable,
            nullable=nullable,
            postgresql_using=f"{col}::text::bigint",  # no-op on empty table
        )

    # ------------------------------------------------------------------
    # 5. Make hashed_password nullable (bot users have no password)
    # ------------------------------------------------------------------
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(length=255),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # 6. Re-add all FK constraints (same semantics, new column types)
    # ------------------------------------------------------------------
    op.create_foreign_key(None, "listings", "users", ["owner_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "rentals", "users", ["student_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "rental_requests", "users", ["requester_id"], ["id"])
    op.create_foreign_key(None, "rental_requests", "users", ["recipient_id"], ["id"])
    op.create_foreign_key(None, "rental_request_messages", "users", ["sender_id"], ["id"])
    op.create_foreign_key(None, "room_messages", "users", ["sender_id"], ["id"])
    op.create_foreign_key(None, "maintenance_reports", "users", ["reporter_id"], ["id"])
    op.create_foreign_key(None, "maintenance_reports", "users", ["recipient_id"], ["id"])
    op.create_foreign_key(None, "payments", "users", ["payer_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "reviews", "users", ["author_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "subscriptions", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "listing_payments", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "favorites", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "notifications", "users", ["user_id"], ["id"])
    op.create_foreign_key(None, "notifications", "users", ["actor_id"], ["id"])


def downgrade() -> None:
    """Reverse: BIGINT PK → UUID PK.

    Like upgrade(), this is a destructive operation on existing data
    (BIGINT IDs cannot be cast back to UUID).  Data will be truncated.
    """
    # Truncate all tables
    op.execute("TRUNCATE TABLE notifications CASCADE")
    op.execute("TRUNCATE TABLE favorites CASCADE")
    op.execute("TRUNCATE TABLE listing_payments CASCADE")
    op.execute("TRUNCATE TABLE subscriptions CASCADE")
    op.execute("TRUNCATE TABLE reviews CASCADE")
    op.execute("TRUNCATE TABLE payments CASCADE")
    op.execute("TRUNCATE TABLE maintenance_reports CASCADE")
    op.execute("TRUNCATE TABLE room_messages CASCADE")
    op.execute("TRUNCATE TABLE rental_request_messages CASCADE")
    op.execute("TRUNCATE TABLE rental_requests CASCADE")
    op.execute("TRUNCATE TABLE rentals CASCADE")
    op.execute("TRUNCATE TABLE listings CASCADE")
    op.execute("TRUNCATE TABLE users CASCADE")

    # Drop FK constraints
    for table, constraint, col, ref in _USER_FK_CONSTRAINTS:
        # Constraints were re-created without explicit names (op.create_foreign_key None)
        # — drop by discovering the actual name via information_schema.
        op.execute(
            f"""
            DO $$
            DECLARE
                v_constraint text;
            BEGIN
                SELECT tc.constraint_name
                  INTO v_constraint
                  FROM information_schema.table_constraints tc
                  JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                 WHERE tc.table_name   = '{table}'
                   AND kcu.column_name = '{col}'
                   AND tc.constraint_type = 'FOREIGN KEY'
                 LIMIT 1;

                IF v_constraint IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE {table} DROP CONSTRAINT ' || quote_ident(v_constraint);
                END IF;
            END;
            $$;
            """
        )

    # Revert hashed_password to NOT NULL (set '' for empty rows)
    op.execute("UPDATE users SET hashed_password = '' WHERE hashed_password IS NULL")
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    # Revert users.id to UUID
    op.execute(
        "ALTER TABLE users ALTER COLUMN id TYPE UUID USING gen_random_uuid()"
    )

    # Revert FK columns to UUID
    fk_col_changes = [
        ("listings", "owner_id", False),
        ("rentals", "student_id", False),
        ("rental_requests", "requester_id", False),
        ("rental_requests", "recipient_id", False),
        ("rental_request_messages", "sender_id", False),
        ("room_messages", "sender_id", False),
        ("maintenance_reports", "reporter_id", False),
        ("maintenance_reports", "recipient_id", False),
        ("payments", "payer_id", True),
        ("reviews", "author_id", False),
        ("subscriptions", "user_id", False),
        ("listing_payments", "user_id", False),
        ("favorites", "user_id", False),
        ("notifications", "user_id", False),
        ("notifications", "actor_id", True),
    ]
    for table, col, nullable in fk_col_changes:
        op.alter_column(
            table,
            col,
            existing_type=sa.BigInteger(),
            type_=postgresql.UUID(as_uuid=True),
            existing_nullable=nullable,
            nullable=nullable,
            postgresql_using=f"gen_random_uuid()",
        )

    # Restore telegram_id column
    op.add_column("users", sa.Column("telegram_id", sa.BigInteger(), nullable=True))
    op.create_unique_constraint("uq_users_telegram_id", "users", ["telegram_id"])
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=False)

    # Re-add FK constraints (UUID)
    op.create_foreign_key(None, "listings", "users", ["owner_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "rentals", "users", ["student_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "rental_requests", "users", ["requester_id"], ["id"])
    op.create_foreign_key(None, "rental_requests", "users", ["recipient_id"], ["id"])
    op.create_foreign_key(None, "rental_request_messages", "users", ["sender_id"], ["id"])
    op.create_foreign_key(None, "room_messages", "users", ["sender_id"], ["id"])
    op.create_foreign_key(None, "maintenance_reports", "users", ["reporter_id"], ["id"])
    op.create_foreign_key(None, "maintenance_reports", "users", ["recipient_id"], ["id"])
    op.create_foreign_key(None, "payments", "users", ["payer_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "reviews", "users", ["author_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "subscriptions", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "listing_payments", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "favorites", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(None, "notifications", "users", ["user_id"], ["id"])
    op.create_foreign_key(None, "notifications", "users", ["actor_id"], ["id"])
