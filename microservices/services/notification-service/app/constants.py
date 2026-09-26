"""Constants shared across the Notification Service."""

API_PREFIX = "/api/v1"
ACCESS_TOKEN_TYPE = "access"

EVENT_QUEUE = "notification-service.events"
EVENT_BOOKING_CREATED = "booking.created"
EVENT_BOOKING_UPDATED = "booking.updated"
EVENT_LISTING_CREATED = "listing.created"
CONSUMED_EVENTS = [EVENT_BOOKING_CREATED, EVENT_BOOKING_UPDATED, EVENT_LISTING_CREATED]

SOURCE_ROOMMATE = "roommate"
BOOKING_CONFIRMED = "confirmed"
BOOKING_REJECTED = "rejected"
BOOKING_CANCELLED = "cancelled"

# Notification types
TYPE_BOOKING_REQUESTED = "booking_requested"
TYPE_ROOMMATE_REQUESTED = "roommate_requested"
TYPE_BOOKING_CONFIRMED = "booking_confirmed"
TYPE_BOOKING_REJECTED = "booking_rejected"
TYPE_BOOKING_CANCELLED = "booking_cancelled"
TYPE_ROOMMATE_AD_POSTED = "roommate_ad_posted"

# Telegram delivery states
TELEGRAM_PENDING = "pending"
TELEGRAM_SENT = "sent"
TELEGRAM_FAILED = "failed"
TELEGRAM_SKIPPED = "skipped"

BOOKINGS_PAGE = "/my-bookings"
