"""Cross-domain read-only Pydantic DTOs (contracts).

These are the ONLY types that may cross domain boundaries.
Domain services return these instead of SQLAlchemy ORM instances
when other domains need to read their data.

RULE: Nothing in this package may import from ``app.domains.*``.
"""
