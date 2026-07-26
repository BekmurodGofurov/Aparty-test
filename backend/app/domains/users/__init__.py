"""Users domain — Auth, Profiles, Notifications.

Internal boundaries:
  - models.py   : User, UserRole, Notification, NotificationType ORM classes
  - schemas.py  : All request/response Pydantic models for this domain
  - services.py : LoginCodeStore, token helpers, user CRUD, auth deps
  - router.py   : /auth/* and /users/* and /notifications/* endpoints

Exports:
  - register_event_handlers : Called by lifespan to wire cross-domain events
"""

from __future__ import annotations


def register_event_handlers() -> None:
    """Subscribe to domain events emitted by other domains.

    Called once during application lifespan startup.
    """
    # Example: when the orders domain confirms a booking, notify the user.
    # from app.core.events import subscribe
    # from app.domains.users.services import notify_user_on_booking_confirmed
    # subscribe("booking.confirmed", notify_user_on_booking_confirmed)
    pass
