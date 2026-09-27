"""Domain constants shared across the Catalog Service."""

API_PREFIX = "/api/v1"

ACCESS_TOKEN_TYPE = "access"
ROLE_OWNER = "owner"
ROLE_MAKLER = "makler"
ROLE_STUDENT = "student"
ALL_ROLES = (ROLE_OWNER, ROLE_MAKLER, ROLE_STUDENT)
LISTING_CREATOR_ROLES = (ROLE_OWNER, ROLE_MAKLER)
# Tenants post roommate ads. The apartment's owner has already let it, so owners are excluded.
ROOMMATE_CREATOR_ROLES = (ROLE_STUDENT, ROLE_MAKLER)
MAX_ROOMMATE_SPACES = 10
MAX_RESIDENTS_PER_GROUP = 20

# Tashkent city center, used when a listing has no coordinates.
DEFAULT_LATITUDE = 41.311081
DEFAULT_LONGITUDE = 69.240562

DEFAULT_LISTING_TITLE = "Listing"
DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 100

ALLOWED_IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp"})
ALLOWED_IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})

TELEGRAM_LINK_BASE = "https://t.me/"

BOOKING_UPDATED_ROUTING_KEY = "booking.updated"
BOOKING_CONSUMER_QUEUE = "catalog-service.booking-events"
