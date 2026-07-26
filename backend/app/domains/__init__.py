"""Domain packages for the Aparty Modular Monolith.

Domains:
  - users      : Auth, profiles, notifications
  - apartments : Listings, search, view-sync daemon, favorites, locations
  - orders     : Bookings, rentals, payments, reviews, subscriptions
  - media      : Photo/video uploads
  - admin      : Cross-cutting admin panel (orchestrates via service calls)

Cross-domain communication rules:
  1. A domain's router.py and services.py MUST NEVER import SQLAlchemy models
     from another domain. Only ``app.core.contracts`` DTOs may cross boundaries.
  2. Synchronous reads use service-to-service calls returning DTOs.
  3. Async side effects use ``app.core.events.publish()``.
"""
