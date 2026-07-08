"""Database migration entry point for manual invocation."""

from app.db_migrations import run_migrations

if __name__ == "__main__":
    run_migrations()
    print("Database migrations applied successfully.")
