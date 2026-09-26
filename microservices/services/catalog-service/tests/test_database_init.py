from sqlalchemy import text

from app.database import init_db
from tests.conftest import LISTING_PAYLOAD, auth_headers


async def test_init_db_removes_legacy_price_usd_column(client, engine):
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE listings ADD COLUMN price_usd integer NOT NULL DEFAULT 0"))
        await conn.execute(text("ALTER TABLE listings ALTER COLUMN price_usd DROP DEFAULT"))

    await init_db()

    async with engine.connect() as conn:
        columns = (await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'listings'"
        ))).scalars().all()
    assert "price_usd" not in columns

    created = await client.post("/api/v1/listings", json=LISTING_PAYLOAD, headers=auth_headers(1))
    assert created.status_code == 201


async def test_init_db_adds_roommate_columns_and_drops_the_old_booking_based_ones(engine):
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE listings DROP COLUMN residents_male, DROP COLUMN expires_at"))
        await conn.execute(text("ALTER TABLE listings ADD COLUMN allow_roommates BOOLEAN NOT NULL DEFAULT FALSE"))
        await conn.execute(text("ALTER TABLE listings ADD COLUMN tenancy_booking_id UUID, ADD COLUMN tenancy_end_date DATE"))

    await init_db()

    async with engine.connect() as conn:
        columns = set((await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'listings'"
        ))).scalars().all())
    assert {"parent_listing_id", "residents_male", "residents_female", "residents_children",
            "available_from", "expires_at"} <= columns
    assert not {"allow_roommates", "tenancy_booking_id", "tenancy_end_date"} & columns
