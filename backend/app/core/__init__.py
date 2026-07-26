"""Core infrastructure layer.

This package contains shared, domain-agnostic utilities:
  - config       : Application settings (Pydantic-Settings)
  - database     : SQLAlchemy async engine, session factory, Base declarative
  - db_migrations: Alembic startup runner
  - redis        : Redis pool factory
  - lifespan     : FastAPI asynccontextmanager startup/shutdown
  - events       : Lightweight in-process domain event bus
  - security     : JWT token creation helper
  - cache        : @cached decorator, @etag decorator, CacheManager, TTL policies
  - contracts    : Cross-domain read-only Pydantic DTOs

RULE: Nothing in this package may import from ``app.domains.*``.
"""
