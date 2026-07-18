import asyncio
import random
from datetime import datetime, timedelta, timezone


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database import engine
from app.models.listing import Listing, ListingSource, ListingTargetGender
from app.models.user import User, UserRole

REGIONS = {
    "Toshkent shahri": ["Yunusobod", "Chilonzor", "Mirzo Ulug'bek", "Yashnobod", "Mirobod", "Shayxontohur", "Uchtepa", "Olmazor", "Yakkasaroy", "Sergeli"],
    "Toshkent viloyati": ["Zangiota", "Qibray", "Chirchiq", "Angren", "Olmaliq", "Bekobod", "Yangiyo'l"],
    "Samarqand": ["Samarqand shahar", "Pastdarg'om", "Ishtixon", "Bulung'ur", "Narpay", "Urgut"],
    "Farg'ona": ["Farg'ona shahar", "Marg'ilon", "Qo'qon", "Quva", "Rishton", "Oltiariq"],
    "Andijon": ["Andijon shahar", "Asaka", "Shahrixon", "Xonobod", "Paxtaobod"],
    "Namangan": ["Namangan shahar", "Chortoq", "Uychi", "Pop", "Kosonsoy"],
    "Buxoro": ["Buxoro shahar", "G'ijduvon", "Kogon", "Vobkent", "Qoraköl"],
    "Qashqadaryo": ["Qarshi", "Shahrisabz", "Kitob", "G'uzor", "Koson"],
    "Surxondaryo": ["Termiz", "Denov", "Sherobod", "Jarqo'rg'on", "Sho'rchi"],
    "Xorazm": ["Urganch", "Xiva", "Gurlan", "Shovot", "Bog'ot"],
    "Navoiy": ["Navoiy shahar", "Zarafshon", "Uchquduq", "Karmana"],
    "Jizzax": ["Jizzax shahar", "Zomin", "G'allaorol", "Paxtakor"],
}

REGION_COORDS = {
    "Toshkent shahri": (41.3111, 69.2797),
    "Toshkent viloyati": (41.0275, 69.3582),
    "Samarqand": (39.6542, 66.9597),
    "Farg'ona": (40.3894, 71.7864),
    "Andijon": (40.7821, 72.3442),
    "Namangan": (41.0011, 71.6726),
    "Buxoro": (39.7747, 64.4286),
    "Qashqadaryo": (38.8610, 65.7847),
    "Surxondaryo": (37.2242, 67.2783),
    "Xorazm": (41.5500, 60.6333),
    "Navoiy": (40.1039, 65.3688),
    "Jizzax": (40.1250, 67.8808),
}

AMENITIES_LIST = ["wifi", "gas", "water", "tv", "ac", "washer", "fridge", "kitchenware"]

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _get_or_create_user(
    session: AsyncSession,
    *,
    phone: str,
    full_name: str,
    role: UserRole,
) -> User:
    result = await session.execute(select(User).where(User.phone == phone))
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    user = User(
        id=int(phone.replace("+", "")),
        full_name=full_name,
        phone=phone,
        role=role,
        is_verified=True,
    )
    session.add(user)
    await session.flush()
    return user


async def seed() -> None:
    async with SessionLocal() as session:
        print("Creating users...")

        for i in range(5):
            await _get_or_create_user(
                session,
                phone=f"+99890111000{i}",
                full_name=f"Admin {i + 1}",
                role=UserRole.admin,
            )

        broker_ids: list[int] = []
        for i in range(100):
            user = await _get_or_create_user(
                session,
                phone=f"+9989022200{i:02d}",
                full_name=f"Broker {i + 1}",
                role=UserRole.makler,
            )
            broker_ids.append(user.id)

        owner_ids: list[int] = []
        for i in range(30):
            user = await _get_or_create_user(
                session,
                phone=f"+9989033300{i:02d}",
                full_name=f"Owner {i + 1}",
                role=UserRole.owner,
            )
            owner_ids.append(user.id)

        for i in range(70):
            await _get_or_create_user(
                session,
                phone=f"+9989044400{i:02d}",
                full_name=f"Student {i + 1}",
                role=UserRole.student,
            )

        await session.commit()

        creators = broker_ids + owner_ids
        now = datetime.now(timezone.utc)

        print("Creating 2000 listings...")
        for i in range(2000):
            region = random.choice(list(REGIONS.keys()))
            district = random.choice(REGIONS[region])
            center_lat, center_lon = REGION_COORDS.get(region, (40.7821, 72.3442))
            owner_id = random.choice(creators)
            is_premium = i < 200
            premium_expires_at = now + timedelta(days=30) if is_premium else None

            amenities = {amenity: random.choice([True, False]) for amenity in AMENITIES_LIST}
            images = ["https://picsum.photos/800/600", "https://picsum.photos/801/601"]
            source = ListingSource.makler if owner_id in broker_ids else ListingSource.owner

            listing = Listing(
                owner_id=owner_id,
                region=region,
                district=district,
                address=f"Street {i}",
                latitude=center_lat + random.uniform(-0.08, 0.08),
                longitude=center_lon + random.uniform(-0.08, 0.08),
                rooms_count=random.randint(1, 5),
                price_usd=random.randint(200, 2000),
                target_gender=random.choice(list(ListingTargetGender)),
                source=source,
                max_guests=4,
                available_spaces=random.randint(1, 4),
                amenities=amenities,
                images=images,
                description="Demo listing",
                is_premium=is_premium,
                premium_expires_at=premium_expires_at,
                is_active=True,
                views_count=random.randint(20, 2500),
                created_at=now,
            )
            session.add(listing)

            if (i + 1) % 500 == 0:
                await session.commit()
                print(f"Inserted {i + 1} listings...")

        await session.commit()

    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
