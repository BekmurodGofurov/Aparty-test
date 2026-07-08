"""Initial schema from ORM models.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = postgresql.ENUM("student", "owner", "makler", "admin", name="user_role", create_type=False)
listing_target_gender = postgresql.ENUM("male", "female", "mixed", name="listing_target_gender", create_type=False)
listing_source = postgresql.ENUM("owner", "makler", "exiting_student", name="listing_source", create_type=False)
payment_status = postgresql.ENUM("paid", "pending", "overdue", name="payment_status", create_type=False)
subscription_type = postgresql.ENUM("owner_monthly", "makler_s", "makler_l", name="subscription_type", create_type=False)
listing_payment_type = postgresql.ENUM("regular", "premium", name="listing_payment_type", create_type=False)
listing_payment_status = postgresql.ENUM("paid", "pending", name="listing_payment_status", create_type=False)
rental_request_status = postgresql.ENUM(
    "pending", "accepted", "rejected", "cancelled", name="rental_request_status", create_type=False
)
maintenance_report_status = postgresql.ENUM(
    "open", "in_progress", "resolved", name="maintenance_report_status", create_type=False
)
notification_type = postgresql.ENUM(
    "rental_request",
    "request_message",
    "request_accepted",
    "request_rejected",
    name="notification_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    listing_target_gender.create(bind, checkfirst=True)
    listing_source.create(bind, checkfirst=True)
    payment_status.create(bind, checkfirst=True)
    subscription_type.create(bind, checkfirst=True)
    listing_payment_type.create(bind, checkfirst=True)
    listing_payment_status.create(bind, checkfirst=True)
    rental_request_status.create(bind, checkfirst=True)
    maintenance_report_status.create(bind, checkfirst=True)
    notification_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("university", sa.String(length=100), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("profile_picture_url", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=False)

    op.create_table(
        "listings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("building_number", sa.String(length=20), nullable=True),
        sa.Column("room_number", sa.String(length=20), nullable=True),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("total_floors", sa.Integer(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("rooms_count", sa.Integer(), nullable=False),
        sa.Column("area_m2", sa.Integer(), nullable=True),
        sa.Column("price_usd", sa.Integer(), nullable=False),
        sa.Column("target_gender", listing_target_gender, nullable=False),
        sa.Column("source", listing_source, nullable=False),
        sa.Column("max_guests", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("available_spaces", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("amenities", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("images", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_premium", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("premium_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("views_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rentals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=True),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("price_usd", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("rental_id", sa.UUID(), nullable=False),
        sa.Column("payer_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("billing_month", sa.Date(), nullable=False),
        sa.Column("status", payment_status, server_default=sa.text("'pending'"), nullable=False),
        sa.Column("payment_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["payer_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rental_id"], ["rentals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("review_text", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("listing_id", "author_id", name="uq_listing_author"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", subscription_type, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("listing_limit", sa.Integer(), nullable=False),
        sa.Column("used_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "listing_payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("type", listing_payment_type, nullable=False),
        sa.Column("status", listing_payment_status, server_default=sa.text("'pending'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rental_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("requester_id", sa.UUID(), nullable=False),
        sa.Column("recipient_id", sa.UUID(), nullable=False),
        sa.Column("status", rental_request_status, server_default=sa.text("'pending'"), nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("rental_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["rental_id"], ["rentals.id"]),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rental_request_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("request_id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["rental_requests.id"]),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "room_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("rental_id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["rental_id"], ["rentals.id"]),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "maintenance_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("rental_id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("reporter_id", sa.UUID(), nullable=False),
        sa.Column("recipient_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("status", maintenance_report_status, server_default=sa.text("'open'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["rental_id"], ["rentals.id"]),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "favorites",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "listing_id", name="_user_listing_favorite_uc"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("body", sa.String(), nullable=True),
        sa.Column("request_id", sa.UUID(), nullable=True),
        sa.Column("listing_id", sa.UUID(), nullable=True),
        sa.Column("target_url", sa.String(length=255), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["request_id"], ["rental_requests.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("favorites")
    op.drop_table("maintenance_reports")
    op.drop_table("room_messages")
    op.drop_table("rental_request_messages")
    op.drop_table("rental_requests")
    op.drop_table("listing_payments")
    op.drop_table("subscriptions")
    op.drop_table("reviews")
    op.drop_table("payments")
    op.drop_table("rentals")
    op.drop_table("listings")
    op.drop_index(op.f("ix_users_phone"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    notification_type.drop(bind, checkfirst=True)
    maintenance_report_status.drop(bind, checkfirst=True)
    rental_request_status.drop(bind, checkfirst=True)
    listing_payment_status.drop(bind, checkfirst=True)
    listing_payment_type.drop(bind, checkfirst=True)
    subscription_type.drop(bind, checkfirst=True)
    payment_status.drop(bind, checkfirst=True)
    listing_source.drop(bind, checkfirst=True)
    listing_target_gender.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
