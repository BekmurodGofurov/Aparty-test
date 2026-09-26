"""Domain constants shared across the Order Service."""

API_PREFIX = "/api/v1"

ACCESS_TOKEN_TYPE = "access"
ROLE_OWNER = "owner"
ROLE_MAKLER = "makler"
ROLE_STUDENT = "student"
ALL_ROLES = (ROLE_OWNER, ROLE_MAKLER, ROLE_STUDENT)
EVENT_BOOKING_CREATED = "booking.created"
EVENT_BOOKING_UPDATED = "booking.updated"

RENTAL_TYPE_SHARED_ROOM = "shared_room"
