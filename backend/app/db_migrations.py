"""Programmatic Alembic migrations on application startup."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, pool

from app.config import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = PROJECT_ROOT / "database" / "alembic.ini"


def _import_models() -> None:
    from app import models  # noqa: F401


def _alembic_config() -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", settings.sync_database_url)
    config.set_main_option("script_location", str(PROJECT_ROOT / "database" / "alembic"))
    return config


def _sync_engine():
    return create_engine(settings.sync_database_url, poolclass=pool.NullPool)


def _metadata_differs(connection) -> bool:
    from app.database import Base

    context = MigrationContext.configure(connection)
    return bool(compare_metadata(context, Base.metadata))


def _stamp_head_if_legacy_schema(engine, alembic_config: Config) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    has_alembic_version = "alembic_version" in tables
    has_app_tables = "users" in tables

    if has_app_tables and not has_alembic_version:
        logger.info("Legacy schema detected without Alembic history; stamping head")
        command.stamp(alembic_config, "head")


def run_migrations() -> None:
    """Upgrade the database and autogenerate revisions when ORM models drift."""
    if not settings.auto_migrate_on_startup:
        logger.info("Startup auto-migration is disabled")
        return

    _import_models()
    alembic_config = _alembic_config()
    engine = _sync_engine()

    try:
        with engine.connect() as connection:
            _stamp_head_if_legacy_schema(connection, alembic_config)

        command.upgrade(alembic_config, "head")

        with engine.connect() as connection:
            if _metadata_differs(connection):
                revision_message = f"auto_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
                logger.info("Model changes detected; autogenerating revision %s", revision_message)
                command.revision(alembic_config, message=revision_message, autogenerate=True)
                command.upgrade(alembic_config, "head")
            else:
                logger.info("Database schema is synchronized with ORM models")
    finally:
        engine.dispose()
