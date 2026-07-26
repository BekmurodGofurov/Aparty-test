"""remove_cross_domain_fks

Revision ID: 10003dccda5e
Revises: c3d4e5f6a7b8
Create Date: 2026-07-26 18:10:25.398734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10003dccda5e'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Apartments Domain
    op.drop_constraint('listings_owner_id_fkey', 'listings', type_='foreignkey')
    op.drop_constraint('favorites_user_id_fkey', 'favorites', type_='foreignkey')
    
    # Orders Domain
    op.drop_constraint('rentals_listing_id_fkey', 'rentals', type_='foreignkey')
    op.drop_constraint('rentals_student_id_fkey', 'rentals', type_='foreignkey')
    
    op.drop_constraint('rental_requests_listing_id_fkey', 'rental_requests', type_='foreignkey')
    op.drop_constraint('rental_requests_requester_id_fkey', 'rental_requests', type_='foreignkey')
    op.drop_constraint('rental_requests_recipient_id_fkey', 'rental_requests', type_='foreignkey')
    
    op.drop_constraint('rental_request_messages_sender_id_fkey', 'rental_request_messages', type_='foreignkey')
    
    op.drop_constraint('room_messages_listing_id_fkey', 'room_messages', type_='foreignkey')
    op.drop_constraint('room_messages_sender_id_fkey', 'room_messages', type_='foreignkey')
    
    op.drop_constraint('maintenance_reports_listing_id_fkey', 'maintenance_reports', type_='foreignkey')
    op.drop_constraint('maintenance_reports_reporter_id_fkey', 'maintenance_reports', type_='foreignkey')
    op.drop_constraint('maintenance_reports_recipient_id_fkey', 'maintenance_reports', type_='foreignkey')
    
    op.drop_constraint('payments_payer_id_fkey', 'payments', type_='foreignkey')
    
    op.drop_constraint('reviews_listing_id_fkey', 'reviews', type_='foreignkey')
    op.drop_constraint('reviews_author_id_fkey', 'reviews', type_='foreignkey')
    
    op.drop_constraint('subscriptions_user_id_fkey', 'subscriptions', type_='foreignkey')
    
    op.drop_constraint('listing_payments_listing_id_fkey', 'listing_payments', type_='foreignkey')
    op.drop_constraint('listing_payments_user_id_fkey', 'listing_payments', type_='foreignkey')


def downgrade() -> None:
    # Notice: we don't implement downgrade here as re-adding constraints might fail if dirty data was inserted in the meantime.
    pass
