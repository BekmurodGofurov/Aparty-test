"""
╔══════════════════════════════════════════════════════════════════════╗
║            Aparty — Comprehensive Demo Data Seed Script              ║
║  Strategy doc: brain/cd0b6211.../demo_data_strategy.md              ║
║                                                                      ║
║  HOW TO RUN (from the `backend/` directory):                        ║
║    python -m scripts.seed_demo_data                                 ║
║    python -m scripts.seed_demo_data --wipe  # wipe then re-seed     ║
║                                                                      ║
║  WHAT IT CREATES:                                                    ║
║    • 8 users   (2 owners, 2 maklers, 4 students — root admin via env)║
║    • 14 listings (premium, regular, deactivated, zero-views…)       ║
║    • 3 subscriptions  (at-cap, expiring, expired)                   ║
║    • 7 listing-payment records                                       ║
║    • 3 rentals + 12 monthly payments (paid/pending/overdue)         ║
║    • 4 rental requests + message thread + room messages             ║
║    • 4 reviews, 4 favorites, 3 maintenance reports, 4 notifications ║
║                                                                      ║
║  IDEMPOTENT: re-running skips rows that already exist.              ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations

import argparse
import asyncio
import ssl
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Build a dedicated engine for the seed script with a generous connect
# timeout so Neon's serverless pool has time to wake up (app engine uses 5 s).
_ssl_ctx = ssl.create_default_context()
_seed_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"ssl": _ssl_ctx, "timeout": 30},
)
AsyncSessionLocal = async_sessionmaker(
    _seed_engine, class_=AsyncSession, expire_on_commit=False
)
from app.models import (
    Favorite,
    Listing,
    ListingPayment,
    ListingPaymentStatus,
    ListingPaymentType,
    ListingSource,
    ListingTargetGender,
    MaintenanceReport,
    MaintenanceReportStatus,
    Notification,
    NotificationType,
    Payment,
    PaymentStatus,
    Rental,
    RentalRequest,
    RentalRequestMessage,
    RentalRequestStatus,
    Review,
    RoomMessage,
    Subscription,
    SubscriptionType,
    User,
    UserRole,
)
# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────
TODAY = date.today()
NOW = datetime.now(timezone.utc)

ANDIJAN_LAT = 40.7821
ANDIJAN_LNG = 72.3442

SAMPLE_IMAGES = [
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1200&q=80",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1200&q=80",
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1200&q=80",
    "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=1200&q=80",
    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=1200&q=80",
]

# Standard English amenity keys: gas, water, ac, washer, fridge, kitchenware, wifi, tv
BASE_AMENITIES: dict[str, bool] = {
    "gas": True,
    "water": True,
    "ac": False,
    "washer": False,
    "fridge": True,
    "kitchenware": True,
    "wifi": True,
    "tv": False,
}

FULL_AMENITIES: dict[str, bool] = {
    "gas": True,
    "water": True,
    "ac": True,
    "washer": True,
    "fridge": True,
    "kitchenware": True,
    "wifi": True,
    "tv": True,
}

# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _coord(lat_off: float, lng_off: float) -> tuple[float, float]:
    return round(ANDIJAN_LAT + lat_off, 6), round(ANDIJAN_LNG + lng_off, 6)

def _dt(days: int) -> datetime:
    return NOW + timedelta(days=days)

def _d(days: int) -> date:
    return TODAY + timedelta(days=days)

async def _get_or_none(db: AsyncSession, model: Any, **filters) -> Any | None:
    return await db.scalar(select(model).filter_by(**filters))

# ─────────────────────────────────────────────────────────────────────
# 1. Users
# ─────────────────────────────────────────────────────────────────────

async def seed_users(db: AsyncSession) -> dict[str, User]:
    print("\n── [1/8] Seeding Users (Telegram BigInteger IDs) ────────────")
    specs = [
        dict(alias="makler_mansur",  id=200000001, full_name="Mansur Holiqov",     phone="+998901000020", role=UserRole.makler,  university=None,                                    is_verified=True),
        dict(alias="makler_gavhar",  id=200000002, full_name="Gavhar Toshmatova",  phone="+998901000021", role=UserRole.makler,  university=None,                                    is_verified=True),
        dict(alias="owner_dilnoza",  id=300000001, full_name="Dilnoza Raximova",   phone="+998901000010", role=UserRole.owner,   university=None,                                    is_verified=True),
        dict(alias="owner_sarvar",   id=300000002, full_name="Sarvar Nazarov",     phone="+998901000011", role=UserRole.owner,   university=None,                                    is_verified=False),
        dict(alias="student_aziz",   id=400000001, full_name="Aziz Mirzayev",      phone="+998901000030", role=UserRole.student, university="Andijon Davlat Universiteti (ADU)",     is_verified=True),
        dict(alias="student_malika", id=400000002, full_name="Malika Sotvoldiyeva", phone="+998901000031", role=UserRole.student, university="Andijon Mashinasozlik Instituti (AMI)", is_verified=True),
        dict(alias="student_jasur",  id=400000003, full_name="Jasur Ergashev",     phone="+998901000032", role=UserRole.student, university="Andijon Tibbiyot Instituti (ATI)",      is_verified=False),
        dict(alias="student_nodira", id=400000004, full_name="Nodira Xasanova",    phone="+998901000033", role=UserRole.student, university="Fergana Politexnika Instituti (FarPI)", is_verified=True),
    ]
    users: dict[str, User] = {}
    for spec in specs:
        alias = spec.pop("alias")
        existing_by_phone = await _get_or_none(db, User, phone=spec["phone"])
        existing_by_id = await _get_or_none(db, User, id=spec["id"])

        if existing_by_phone and existing_by_id and existing_by_phone.id == existing_by_id.id:
            print(f"  ↩  {alias} already exists (BigInteger ID: {existing_by_phone.id}).")
            users[alias] = existing_by_phone
            continue

        # If there is an older demo user with the same phone but old schema/ID, remove it to ensure exact BigInteger Telegram ID
        if existing_by_phone and existing_by_phone.id != spec["id"]:
            print(f"  🔄 Re-aligning schema ID for {alias}: replacing ID {existing_by_phone.id} with BigInteger {spec['id']}")
            await db.execute(delete(User).where(User.id == existing_by_phone.id))
            await db.flush()
            existing_by_phone = None

        if existing_by_id:
            existing_by_id.full_name = spec["full_name"]
            existing_by_id.phone = spec["phone"]
            existing_by_id.role = spec["role"]
            existing_by_id.university = spec["university"]
            existing_by_id.is_verified = spec["is_verified"]
            print(f"  ✓  {alias} ({spec['phone']}) updated with BigInteger ID: {spec['id']}.")
            users[alias] = existing_by_id
            continue

        user = User(**spec)
        db.add(user)
        await db.flush()
        print(f"  ✓  {alias} ({spec['phone']}) created with BigInteger ID: {spec['id']}.")
        users[alias] = user
    await db.commit()
    for u in users.values():
        await db.refresh(u)
    return users

# ─────────────────────────────────────────────────────────────────────
# 2. Listings
# ─────────────────────────────────────────────────────────────────────

async def seed_listings(db: AsyncSession, users: dict[str, User]) -> dict[str, Listing]:
    print("\n── [2/9] Seeding Listings ───────────────────────────────────")

    def L(alias, owner_key, district, address, building_number, room_number,
          floor, total_floors, lat_off, lng_off, rooms_count, area_m2, price_usd,
          target_gender, source, max_guests, available_spaces, amenities, img_idx,
          description, is_premium, premium_days, is_active, views_count):
        lat, lng = _coord(lat_off, lng_off)
        images_sel = [SAMPLE_IMAGES[i % 5] for i in range(img_idx, img_idx + 2)]
        return dict(
            alias=alias, owner_key=owner_key,
            region="Andijon", district=district, address=address,
            building_number=building_number, room_number=room_number,
            floor=floor, total_floors=total_floors,
            latitude=lat, longitude=lng,
            rooms_count=rooms_count, area_m2=area_m2, price_usd=price_usd,
            target_gender=target_gender, source=source,
            max_guests=max_guests, available_spaces=available_spaces,
            amenities=amenities, images=images_sel,
            description=description,
            is_premium=is_premium,
            premium_expires_at=(_dt(premium_days) if premium_days is not None else None),
            is_active=is_active, views_count=views_count,
        )

    specs = [
        L("L01", "owner_dilnoza",  "Asaka",          "Navruz ko'chasi 12, Asaka",              "12", "3",  3, 5,  0.012,  0.024,  2, 45, 120, ListingTargetGender.male,   ListingSource.owner,   2, 1, {**BASE_AMENITIES, "washer": True},                       0, "Asaka tumanida qulay 2 xonali xonadon. Wi-Fi, kir yuvish mashina mavjud. Faqat erkak talabalar.",                               True,  20, True,  1247),
        L("L02", "owner_dilnoza",  "Oltinkol",        "Mustaqillik ko'chasi 7, Oltinkol",        "7",  "1",  1, 3, -0.018,  0.031,  1, 28,  75, ListingTargetGender.female, ListingSource.owner,   1, 1, {**BASE_AMENITIES},                                                  2, "Oltinkol tumanida 1 xonali xonadon. Faqat qiz talabalar. Isitish tizimi ajoyib.",                                                 False, None, True,    38),
        L("L03", "owner_sarvar",   "Marhamat",        "Bog'bon ko'chasi 5, Marhamat",            "5",  "2",  2, 4,  0.032, -0.015,  3, 70, 150, ListingTargetGender.mixed,  ListingSource.owner,   3, 3, {**BASE_AMENITIES},                                                  3, "Marhamat tumanida 3 xonali keng xonadon. Hozirda ta'mirda. Egasi tasdiqlanmagan.",                                               False, None, False,     5),
        L("L04", "owner_sarvar",   "Andijon shahri",  "Istiqlol ko'chasi 22, Andijon shahri",   "22", "4",  4, 9,  0.005,  0.003,  1, 22,  90, ListingTargetGender.male,   ListingSource.owner,   1, 1, {**BASE_AMENITIES, "ac": True},                        4, "Andijon markazida 1 xonali. Premium status muddati tugashiga 2 kun qoldi!",                                                      True,   2, True,   201),
        L("L05", "makler_mansur",  "Qo'rg'ontepa",   "Sharq ko'chasi 8, Qo'rg'ontepa",         "8",  "5",  2, 5, -0.041,  0.058,  2, 52, 100, ListingTargetGender.mixed,  ListingSource.makler,  2, 2, {**BASE_AMENITIES, "washer": True, "ac": True}, 0, "Qo'rg'ontepa tumanida 2 xonali. Wi-Fi, konditsioner, parking. Makler orqali.",                                False, None, True,   456),
        L("L06", "makler_mansur",  "Asaka",           "Yangi hayot ko'chasi 3, Asaka",           "3",  "7",  1, 2,  0.019,  0.027,  1, 30,  80, ListingTargetGender.female, ListingSource.makler,  1, 1, {**BASE_AMENITIES},                                                  1, "Asaka tumanida qiz talabalar uchun xona. Makler orqali.",                                                                         False, None, True,    92),
        L("L07", "makler_mansur",  "Shahrixon",       "Do'stlik ko'chasi 14, Shahrixon",        "14", "2",  3, 5, -0.055, -0.022,  2, 48, 110, ListingTargetGender.male,   ListingSource.makler,  2, 2, {**BASE_AMENITIES, "washer": True},                        3, "Shahrixon tumanida 2 xonali. Erkak talabalar uchun.",                                                                             False, None, True,    17),
        L("L08", "makler_mansur",  "Baliqchi",        "Tinchlik ko'chasi 19, Baliqchi",         "19", "1",  1, 3,  0.061, -0.044,  3, 65, 130, ListingTargetGender.mixed,  ListingSource.makler,  3, 3, {**BASE_AMENITIES},                                4, "Baliqchi tumanida yangi e'lon. Hali hech kim ko'rmagan.",                                                                         False, None, True,     0),
        L("L09", "makler_mansur",  "Xo'jaobod",      "Baxt ko'chasi 6, Xo'jaobod",              "6",  "3",  2, 4, -0.071,  0.039,  1, 20,  60, ListingTargetGender.male,   ListingSource.makler,  1, 1, {**BASE_AMENITIES},                                                  0, "Xo'jaobod tumanida eng arzon variant. Maklerning 5-chi (oxirgi) e'loni.",                                                        False, None, True,     3),
        L("L10", "makler_gavhar",  "Andijon shahri",  "Navoiy ko'chasi 33, Andijon shahri",     "33", "8",  2, 4,  0.003,  0.007,  2, 40, 115, ListingTargetGender.female, ListingSource.makler,  2, 1, {**FULL_AMENITIES},                                                  1, "Andijon markazida premium 2 xonali. Barcha qulayliklar: Wi-Fi, AC, parking, sport zal. Qiz talabalar.",                          True,  25, True,   834),
        L("L11", "makler_gavhar",  "Izboskan",        "Guliston ko'chasi 11, Izboskan",         "11", "2",  5, 9, -0.028, -0.033,  3, 72, 140, ListingTargetGender.mixed,  ListingSource.makler,  3, 2, {**FULL_AMENITIES},                                                  0, "Izboskan tumanida keng 3 xonali premium xonadon. Oila yoki guruh uchun.",                                                        True,  25, True,   312),
        L("L12", "makler_gavhar",  "Oltinkol",        "Mehnat ko'chasi 4, Oltinkol",             "4",  "6",  1, 2, -0.022,  0.044,  1, 25,  70, ListingTargetGender.male,   ListingSource.makler,  1, 1, {**BASE_AMENITIES, "washer": True},                        2, "Oltinkol tumanida arzon 1 xonali. Erkak talabalar uchun.",                                                                        False, None, True,    55),
        L("L13", "owner_dilnoza",  "Asaka",           "Bog'cha ko'chasi 1, Asaka",               "1",  "9",  1, 2,  0.008,  0.021,  1, 18,  50, ListingTargetGender.mixed,  ListingSource.owner,   1, 1, {**BASE_AMENITIES},                                                  3, "Asaka tumanida eng arzon variant ($50). Talabalar uchun iqtisodiy xona.",                                                         False, None, True,     9),
        L("L14", "makler_gavhar",  "Jalaquduq",       "Yoshlik ko'chasi 2, Jalaquduq",           "2",  "1",  2, 3,  0.044, -0.062,  2, 38,  95, ListingTargetGender.female, ListingSource.makler,  2, 2, {**BASE_AMENITIES, "ac": True},                        1, "Jalaquduq tumanida yangi e'lon. 0 ko'rilgan. Qiz talabalar uchun 2 xonali.",                                                      False, None, True,     0),
    ]

    listings: dict[str, Listing] = {}
    for spec in specs:
        alias = spec.pop("alias")
        owner = users[spec.pop("owner_key")]
        spec["owner_id"] = owner.id

        existing = await _get_or_none(db, Listing, owner_id=owner.id, address=spec["address"])
        if existing:
            print(f"  ↩  {alias} already exists.")
            listings[alias] = existing
            continue

        listing = Listing(**spec)
        db.add(listing)
        await db.flush()
        print(f"  ✓  {alias} → {spec['district']} / ${spec['price_usd']} / views={spec['views_count']} / premium={spec['is_premium']}")
        listings[alias] = listing

    await db.commit()
    for lst in listings.values():
        await db.refresh(lst)
    return listings

# ─────────────────────────────────────────────────────────────────────
# 3. Subscriptions
# ─────────────────────────────────────────────────────────────────────

async def seed_subscriptions(db: AsyncSession, users: dict[str, User]) -> None:
    print("\n── [3/9] Seeding Subscriptions ─────────────────────────────")
    specs = [
        dict(alias="sub_mansur",          user_key="makler_mansur", type=SubscriptionType.makler_s,      start_date=_d(-30), end_date=_d(0),  listing_limit=5,   used_count=5, is_active=True),
        dict(alias="sub_gavhar",          user_key="makler_gavhar", type=SubscriptionType.makler_l,      start_date=_d(-30), end_date=_d(3),  listing_limit=100, used_count=3, is_active=True),
        dict(alias="sub_dilnoza_expired", user_key="owner_dilnoza", type=SubscriptionType.owner_monthly, start_date=_d(-60), end_date=_d(-30),listing_limit=1,   used_count=1, is_active=False),
    ]
    for spec in specs:
        alias = spec.pop("alias")
        user = users[spec.pop("user_key")]
        existing = await _get_or_none(db, Subscription, user_id=user.id, type=spec["type"], start_date=spec["start_date"])
        if existing:
            print(f"  ↩  {alias} already exists.")
            continue
        sub = Subscription(user_id=user.id, **spec)
        db.add(sub)
        print(f"  ✓  {alias}: {spec['type'].value} limit={spec['listing_limit']} used={spec['used_count']} end={spec['end_date']} active={spec['is_active']}")
    await db.commit()

# ─────────────────────────────────────────────────────────────────────
# 4. Listing Payments
# ─────────────────────────────────────────────────────────────────────

async def seed_listing_payments(db: AsyncSession, users: dict[str, User], listings: dict[str, Listing]) -> None:
    print("\n── [4/9] Seeding Listing Payments ──────────────────────────")
    specs = [
        dict(alias="lp_L01", listing_key="L01", user_key="owner_dilnoza",  type=ListingPaymentType.premium, amount=40, status=ListingPaymentStatus.paid),
        dict(alias="lp_L04", listing_key="L04", user_key="owner_sarvar",   type=ListingPaymentType.premium, amount=40, status=ListingPaymentStatus.paid),
        dict(alias="lp_L10", listing_key="L10", user_key="makler_gavhar",  type=ListingPaymentType.premium, amount=30, status=ListingPaymentStatus.paid),
        dict(alias="lp_L11", listing_key="L11", user_key="makler_gavhar",  type=ListingPaymentType.premium, amount=30, status=ListingPaymentStatus.paid),
        dict(alias="lp_L05", listing_key="L05", user_key="makler_mansur",  type=ListingPaymentType.regular,  amount=3,  status=ListingPaymentStatus.paid),
        dict(alias="lp_L02", listing_key="L02", user_key="owner_dilnoza",  type=ListingPaymentType.regular,  amount=5,  status=ListingPaymentStatus.paid),
        dict(alias="lp_L13", listing_key="L13", user_key="owner_dilnoza",  type=ListingPaymentType.regular,  amount=5,  status=ListingPaymentStatus.pending),
    ]
    for spec in specs:
        alias = spec.pop("alias")
        listing = listings[spec.pop("listing_key")]
        user = users[spec.pop("user_key")]
        existing = await _get_or_none(db, ListingPayment, listing_id=listing.id, type=spec["type"])
        if existing:
            print(f"  ↩  {alias} already exists.")
            continue
        db.add(ListingPayment(listing_id=listing.id, user_id=user.id, **spec))
        print(f"  ✓  {alias}: ${spec['amount']} {spec['type'].value} / {spec['status'].value}")
    await db.commit()

# ─────────────────────────────────────────────────────────────────────
# 5. Rentals
# ─────────────────────────────────────────────────────────────────────

async def seed_rentals(db: AsyncSession, users: dict[str, User], listings: dict[str, Listing]) -> dict[str, Rental]:
    print("\n── [5/9] Seeding Rentals ────────────────────────────────────")
    specs = [
        dict(alias="rental_aziz_dilnoza",  student_key="student_aziz",   listing_key="L01", start_date=date(2026, 3, 1), end_date=None,              price_usd=120, is_active=True),
        dict(alias="rental_jasur_old",     student_key="student_jasur",  listing_key="L05", start_date=date(2025, 9, 1), end_date=date(2025, 12, 31),price_usd=100, is_active=False),
        dict(alias="rental_malika_gavhar", student_key="student_malika", listing_key="L10", start_date=date(2026, 5, 1), end_date=None,              price_usd=115, is_active=True),
    ]
    rentals: dict[str, Rental] = {}
    for spec in specs:
        alias = spec.pop("alias")
        student = users[spec.pop("student_key")]
        listing = listings[spec.pop("listing_key")]
        existing = await _get_or_none(db, Rental, student_id=student.id, listing_id=listing.id, start_date=spec["start_date"])
        if existing:
            print(f"  ↩  {alias} already exists.")
            rentals[alias] = existing
            continue
        rental = Rental(student_id=student.id, listing_id=listing.id, **spec)
        db.add(rental)
        await db.flush()
        label = "ACTIVE" if spec["is_active"] else "COMPLETED"
        print(f"  ✓  {alias} [{label}] ${spec['price_usd']}/mo")
        rentals[alias] = rental
    await db.commit()
    for r in rentals.values():
        await db.refresh(r)
    return rentals

# ─────────────────────────────────────────────────────────────────────
# 6. Payments
# ─────────────────────────────────────────────────────────────────────

async def seed_payments(db: AsyncSession, users: dict[str, User], rentals: dict[str, Rental]) -> None:
    print("\n── [6/9] Seeding Payments ───────────────────────────────────")

    def P(alias, rk, pk, amount, bm, status, pd=None):
        return dict(alias=alias, rental_key=rk, payer_key=pk, amount=amount,
                    billing_month=bm, status=status, payment_date=pd)

    DT = lambda y, m, d, h=10: datetime(y, m, d, h, 0, tzinfo=timezone.utc)

    specs = [
        # Rental A — aziz/dilnoza $120/mo
        P("pay_A_mar", "rental_aziz_dilnoza",  "student_aziz",   120, date(2026,3,1),  PaymentStatus.paid,    DT(2026,3,2)),
        P("pay_A_apr", "rental_aziz_dilnoza",  "student_aziz",   120, date(2026,4,1),  PaymentStatus.paid,    DT(2026,4,1,9)),
        P("pay_A_may", "rental_aziz_dilnoza",  "student_aziz",   120, date(2026,5,1),  PaymentStatus.paid,    DT(2026,5,3,14)),
        P("pay_A_jun", "rental_aziz_dilnoza",  "student_aziz",   120, date(2026,6,1),  PaymentStatus.overdue),   # ← OVERDUE
        P("pay_A_jul", "rental_aziz_dilnoza",  "student_aziz",   120, date(2026,7,1),  PaymentStatus.pending),   # ← PENDING
        # Rental B — jasur/mansur $100/mo (completed)
        P("pay_B_sep", "rental_jasur_old",     "student_jasur",  100, date(2025,9,1),  PaymentStatus.paid,    DT(2025,9,1,8)),
        P("pay_B_oct", "rental_jasur_old",     "student_jasur",  100, date(2025,10,1), PaymentStatus.paid,    DT(2025,10,5,11)),
        P("pay_B_nov", "rental_jasur_old",     "student_jasur",  100, date(2025,11,1), PaymentStatus.paid,    DT(2025,11,2,9)),
        P("pay_B_dec", "rental_jasur_old",     "student_jasur",  100, date(2025,12,1), PaymentStatus.paid,    DT(2025,12,3)),
        # Rental C — malika/gavhar $115/mo
        P("pay_C_may", "rental_malika_gavhar", "student_malika", 115, date(2026,5,1),  PaymentStatus.paid,    DT(2026,5,2,9)),
        P("pay_C_jun", "rental_malika_gavhar", "student_malika", 115, date(2026,6,1),  PaymentStatus.paid,    DT(2026,6,1)),
        P("pay_C_jul", "rental_malika_gavhar", "student_malika", 115, date(2026,7,1),  PaymentStatus.pending),   # ← PENDING
    ]

    for spec in specs:
        alias = spec.pop("alias")
        rental = rentals[spec.pop("rental_key")]
        payer = users[spec.pop("payer_key")]
        existing = await _get_or_none(db, Payment, rental_id=rental.id, billing_month=spec["billing_month"])
        if existing:
            print(f"  ↩  {alias} already exists.")
            continue
        db.add(Payment(rental_id=rental.id, payer_id=payer.id, **spec))
        print(f"  ✓  {alias}: ${spec['amount']} [{spec['status'].value}] {spec['billing_month']}")
    await db.commit()

# ─────────────────────────────────────────────────────────────────────
# 7. Rental Requests + Messages
# ─────────────────────────────────────────────────────────────────────

async def seed_rental_requests(
    db: AsyncSession,
    users: dict[str, User],
    listings: dict[str, Listing],
    rentals: dict[str, Rental],
) -> dict[str, RentalRequest]:
    print("\n── [7/9] Seeding Rental Requests & Messages ─────────────────")
    specs = [
        dict(alias="req_malika_l06", listing_key="L06", requester_key="student_malika", recipient_key="makler_mansur", status=RentalRequestStatus.pending,   message="Salom, xonangizni ijaraga olmoqchiman. AMI talabasi. Hujjatlarim tayyor.", rental_key=None),
        dict(alias="req_aziz_l01",   listing_key="L01", requester_key="student_aziz",   recipient_key="owner_dilnoza", status=RentalRequestStatus.accepted,  message="Assalomu alaykum, xonaingiz bo'yicha murojaat qilmoqchiman. ADU talabasi.", rental_key="rental_aziz_dilnoza"),
        dict(alias="req_jasur_l07",  listing_key="L07", requester_key="student_jasur",  recipient_key="makler_mansur", status=RentalRequestStatus.rejected,  message="Xona bo'sh bo'lsa, ijaraga olmoqchiman.", rental_key=None),
        dict(alias="req_nodira_l02", listing_key="L02", requester_key="student_nodira", recipient_key="owner_dilnoza", status=RentalRequestStatus.cancelled, message="Salom, xonangizni ko'rib chiqmoqchiman.", rental_key=None),
    ]
    requests: dict[str, RentalRequest] = {}
    for spec in specs:
        alias = spec.pop("alias")
        listing = listings[spec.pop("listing_key")]
        requester = users[spec.pop("requester_key")]
        recipient = users[spec.pop("recipient_key")]
        rk = spec.pop("rental_key")
        rental_id = rentals[rk].id if rk else None

        existing = await _get_or_none(db, RentalRequest, listing_id=listing.id, requester_id=requester.id)
        if existing:
            print(f"  ↩  {alias} already exists.")
            requests[alias] = existing
            continue
        req = RentalRequest(listing_id=listing.id, requester_id=requester.id, recipient_id=recipient.id, rental_id=rental_id, **spec)
        db.add(req)
        await db.flush()
        print(f"  ✓  {alias} [{spec['status'].value}]")
        requests[alias] = req
    await db.commit()
    for r in requests.values():
        await db.refresh(r)

    # Message thread on pending request
    pending = requests.get("req_malika_l06")
    if pending:
        existing_msg = await _get_or_none(db, RentalRequestMessage, request_id=pending.id)
        if not existing_msg:
            thread = [
                ("student_malika", "Salom, xonangizni ijaraga olmoqchiman. AMI talabasi."),
                ("makler_mansur",  "Salom, qaysi universitetda o'qiysiz?"),
                ("student_malika", "Andijon Mashinasozlik Institutida. 2-kurs."),
            ]
            for sender_key, text in thread:
                db.add(RentalRequestMessage(request_id=pending.id, sender_id=users[sender_key].id, text=text))
            await db.commit()
            print("  ✓  3 messages added to req_malika_l06 thread.")

    return requests

# ─────────────────────────────────────────────────────────────────────
# 7b. Room Messages
# ─────────────────────────────────────────────────────────────────────

async def seed_room_messages(db: AsyncSession, users: dict[str, User], listings: dict[str, Listing], rentals: dict[str, Rental]) -> None:
    rental = rentals["rental_aziz_dilnoza"]
    listing = listings["L01"]
    if await _get_or_none(db, RoomMessage, rental_id=rental.id):
        print("  ↩  Room messages already exist.")
        return
    thread = [
        ("student_aziz",  "Salom, uy egasi, kranda suv bosimi past bo'lib qoldi."),
        ("owner_dilnoza", "Salom Aziz, tezda ko'rib chiqamiz. Rahmat xabar bergani uchun."),
        ("student_aziz",  "Yaxshi, kutaman."),
        ("owner_dilnoza", "Muammo hal qilindi, usta keldi va tuzatdi."),
        ("student_aziz",  "Ajoyib! Rahmat!"),
    ]
    for sender_key, text in thread:
        db.add(RoomMessage(rental_id=rental.id, listing_id=listing.id, sender_id=users[sender_key].id, text=text))
    await db.commit()
    print("  ✓  5 room messages added to Rental A chat.")

# ─────────────────────────────────────────────────────────────────────
# 8. Reviews
# ─────────────────────────────────────────────────────────────────────

async def seed_reviews(db: AsyncSession, users: dict[str, User], listings: dict[str, Listing]) -> None:
    print("\n── [8/9] Seeding Reviews ────────────────────────────────────")
    specs = [
        dict(alias="review_aziz_l01",   listing_key="L01", author_key="student_aziz",   rating=4, review_text="Xona yaxshi, uy egasi juda muomilali. Bir kamchilik — parking yo'q."),
        dict(alias="review_jasur_l05",  listing_key="L05", author_key="student_jasur",  rating=3, review_text="O'rtacha. Isitish tizimi yaxshi, lekin internet sekin edi."),
        dict(alias="review_malika_l10", listing_key="L10", author_key="student_malika", rating=5, review_text="Ajoyib xona! Gavhar opa juda yordam berdi. 100% tavsiya etaman!"),
        dict(alias="review_nodira_l10", listing_key="L10", author_key="student_nodira", rating=None, review_text=None),  # ← null review
    ]
    for spec in specs:
        alias = spec.pop("alias")
        listing = listings[spec.pop("listing_key")]
        author = users[spec.pop("author_key")]
        existing = await _get_or_none(db, Review, listing_id=listing.id, author_id=author.id)
        if existing:
            print(f"  ↩  {alias} already exists.")
            continue
        db.add(Review(listing_id=listing.id, author_id=author.id, **spec))
        rating_str = f"{spec['rating']}★" if spec["rating"] else "null"
        print(f"  ✓  {alias}: rating={rating_str}")
    await db.commit()

# ─────────────────────────────────────────────────────────────────────
# 9a. Favorites
# ─────────────────────────────────────────────────────────────────────

async def seed_favorites(db: AsyncSession, users: dict[str, User], listings: dict[str, Listing]) -> None:
    print("\n── [9/9] Seeding Favorites, Maintenance & Notifications ─────")
    print("   ↳ Favorites:")
    fav_specs = [
        ("student_nodira", "L01"),
        ("student_nodira", "L10"),
        ("student_aziz",   "L10"),
        ("student_malika", "L06"),
    ]
    for uk, lk in fav_specs:
        user, listing = users[uk], listings[lk]
        if await _get_or_none(db, Favorite, user_id=user.id, listing_id=listing.id):
            print(f"     ↩  {uk} → {lk} exists.")
            continue
        db.add(Favorite(user_id=user.id, listing_id=listing.id))
        print(f"     ✓  {uk} → {lk}")
    await db.commit()

# ─────────────────────────────────────────────────────────────────────
# 9b. Maintenance Reports
# ─────────────────────────────────────────────────────────────────────

async def seed_maintenance_reports(
    db: AsyncSession,
    users: dict[str, User],
    listings: dict[str, Listing],
    rentals: dict[str, Rental],
) -> None:
    print("   ↳ Maintenance Reports:")
    specs = [
        dict(alias="report_open",        rental_key="rental_aziz_dilnoza",  listing_key="L01", reporter_key="student_aziz",   recipient_key="owner_dilnoza",  text="Hammom krani singan, suv oqmoqda. Tezda tuzating.",    status=MaintenanceReportStatus.open),
        dict(alias="report_in_progress", rental_key="rental_malika_gavhar", listing_key="L10", reporter_key="student_malika", recipient_key="makler_gavhar",  text="Konditsioner to'g'ri ishlamayapti. Kunduzi juda issiq.", status=MaintenanceReportStatus.in_progress),
        dict(alias="report_resolved",    rental_key="rental_aziz_dilnoza",  listing_key="L01", reporter_key="student_aziz",   recipient_key="owner_dilnoza",  text="Eshik qulfi ishlamayapti.",                             status=MaintenanceReportStatus.resolved),
    ]
    for spec in specs:
        alias = spec.pop("alias")
        rental  = rentals[spec.pop("rental_key")]
        listing = listings[spec.pop("listing_key")]
        reporter = users[spec.pop("reporter_key")]
        recipient = users[spec.pop("recipient_key")]
        existing = await db.scalar(select(MaintenanceReport).where(
            MaintenanceReport.rental_id == rental.id,
            MaintenanceReport.reporter_id == reporter.id,
            MaintenanceReport.text == spec["text"],
        ))
        if existing:
            print(f"     ↩  {alias} exists.")
            continue
        db.add(MaintenanceReport(rental_id=rental.id, listing_id=listing.id, reporter_id=reporter.id, recipient_id=recipient.id, **spec))
        print(f"     ✓  {alias}: [{spec['status'].value}]")
    await db.commit()

# ─────────────────────────────────────────────────────────────────────
# 9c. Notifications
# ─────────────────────────────────────────────────────────────────────

async def seed_notifications(
    db: AsyncSession,
    users: dict[str, User],
    listings: dict[str, Listing],
    requests: dict[str, RentalRequest],
) -> None:
    print("   ↳ Notifications:")
    specs = [
        dict(alias="notif_mansur_request",  user_key="makler_mansur",  actor_key="student_malika", type=NotificationType.rental_request,  title="Yangi ijara so'rovi: Malika Sotvoldiyeva",    body="Malika Sotvoldiyeva sizning e'loningizga so'rov yubordi.", req_key="req_malika_l06", listing_key="L06", is_read=False),
        dict(alias="notif_malika_message",  user_key="student_malika", actor_key="makler_mansur",  type=NotificationType.request_message,  title="Mansur Holiqov javob yozdi",                  body="So'rovingizga yangi xabar keldi.",                          req_key="req_malika_l06", listing_key="L06", is_read=False),
        dict(alias="notif_aziz_accepted",   user_key="student_aziz",   actor_key="owner_dilnoza",  type=NotificationType.request_accepted, title="Ijara so'rovingiz qabul qilindi!",             body="Dilnoza Raximova sizning so'rovingizni qabul qildi.",       req_key="req_aziz_l01",   listing_key="L01", is_read=True),
        dict(alias="notif_jasur_rejected",  user_key="student_jasur",  actor_key="makler_mansur",  type=NotificationType.request_rejected, title="Ijara so'rovingiz rad etildi",                 body="Mansur Holiqov sizning so'rovingizni rad etdi.",            req_key="req_jasur_l07",  listing_key="L07", is_read=True),
    ]
    for spec in specs:
        alias = spec.pop("alias")
        user    = users[spec.pop("user_key")]
        actor   = users[spec.pop("actor_key")]
        listing = listings[spec.pop("listing_key")]
        req     = requests.get(spec.pop("req_key"))
        existing = await db.scalar(select(Notification).where(
            Notification.user_id == user.id,
            Notification.type == spec["type"],
            Notification.title == spec["title"],
        ))
        if existing:
            print(f"     ↩  {alias} exists.")
            continue
        db.add(Notification(user_id=user.id, actor_id=actor.id, listing_id=listing.id, request_id=(req.id if req else None), **spec))
        print(f"     ✓  {alias}: [{'UNREAD' if not spec['is_read'] else 'READ'}] {spec['title'][:45]}")
    await db.commit()

# ─────────────────────────────────────────────────────────────────────
# WIPE
# ─────────────────────────────────────────────────────────────────────

DEMO_PHONES = [
    "+998901000001", "+998901000010", "+998901000011",
    "+998901000020", "+998901000021",
    "+998901000030", "+998901000031", "+998901000032", "+998901000033",
]

DEMO_USER_IDS = [
    100000001, 200000001, 200000002, 300000001, 300000002, 400000001, 400000002, 400000003, 400000004,
    100000010, 100000011, 100000012, 100000013, 100000014, 100000015, 100000016, 100000017, 100000018,
]

async def wipe_demo_data(db: AsyncSession) -> None:
    print("\n⚠️  WIPE MODE — deleting existing demo data...")
    result = await db.execute(
        select(User.id).where(
            (User.phone.in_(DEMO_PHONES)) | (User.id.in_(DEMO_USER_IDS))
        )
    )
    user_ids = [r[0] for r in result.fetchall()]
    if not user_ids:
        print("  — No demo users found.")
        return

    await db.execute(delete(Notification).where(Notification.user_id.in_(user_ids)))
    await db.execute(delete(Notification).where(Notification.actor_id.in_(user_ids)))

    rental_ids = [r[0] for r in (await db.execute(select(Rental.id).where(Rental.student_id.in_(user_ids)))).fetchall()]
    if rental_ids:
        await db.execute(delete(MaintenanceReport).where(MaintenanceReport.rental_id.in_(rental_ids)))
        await db.execute(delete(RoomMessage).where(RoomMessage.rental_id.in_(rental_ids)))
        await db.execute(delete(Payment).where(Payment.rental_id.in_(rental_ids)))

    req_ids = [r[0] for r in (await db.execute(select(RentalRequest.id).where(RentalRequest.requester_id.in_(user_ids)))).fetchall()]
    if req_ids:
        await db.execute(delete(RentalRequestMessage).where(RentalRequestMessage.request_id.in_(req_ids)))
        await db.execute(delete(RentalRequest).where(RentalRequest.id.in_(req_ids)))

    if rental_ids:
        await db.execute(delete(Rental).where(Rental.id.in_(rental_ids)))

    listing_ids = [r[0] for r in (await db.execute(select(Listing.id).where(Listing.owner_id.in_(user_ids)))).fetchall()]
    if listing_ids:
        await db.execute(delete(Review).where(Review.listing_id.in_(listing_ids)))
        await db.execute(delete(Favorite).where(Favorite.listing_id.in_(listing_ids)))
        await db.execute(delete(ListingPayment).where(ListingPayment.listing_id.in_(listing_ids)))
        await db.execute(delete(Listing).where(Listing.id.in_(listing_ids)))

    await db.execute(delete(Subscription).where(Subscription.user_id.in_(user_ids)))
    await db.execute(delete(Review).where(Review.author_id.in_(user_ids)))
    await db.execute(delete(Favorite).where(Favorite.user_id.in_(user_ids)))
    await db.execute(delete(User).where(User.id.in_(user_ids)))
    await db.commit()
    print(f"  ✓  Wiped {len(user_ids)} demo users and all related rows.")

# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

async def main(wipe: bool = False) -> None:
    print("═" * 62)
    print("  Aparty — Demo Data Seed Script (Telegram BigInteger Schema)")
    print("═" * 62)

    async with AsyncSessionLocal() as db:
        try:
            if wipe:
                await wipe_demo_data(db)

            # Relational Integrity sequence:
            # 1. Users first (with BigInteger Telegram IDs)
            users = await seed_users(db)
            # 2. Subscriptions second
            await seed_subscriptions(db, users)
            # 3. Listings third (explicitly linking to BigInteger owner IDs)
            listings = await seed_listings(db, users)
            # 4. Listing Payments
            await seed_listing_payments(db, users, listings)
            # 5. Rentals
            rentals = await seed_rentals(db, users, listings)
            # 6. Payments
            await seed_payments(db, users, rentals)
            # 7. Rental Requests + Messages
            requests = await seed_rental_requests(db, users, listings, rentals)
            # 8. Room Messages
            await seed_room_messages(db, users, listings, rentals)
            # 9. Reviews
            await seed_reviews(db, users, listings)
            # 10. Favorites
            await seed_favorites(db, users, listings)
            # 11. Maintenance Reports
            await seed_maintenance_reports(db, users, listings, rentals)
            # 12. Notifications
            await seed_notifications(db, users, listings, requests)

            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"\n❌ ERROR during seeding: {e}")
            print("🔄 Session rolled back to preserve transactional relational integrity.")
            raise

    print("\n" + "═" * 62)
    print("  ✅  Demo data seeded successfully!")
    print("═" * 62)
    print("\n  Authentication: 100% Passwordless (Telegram Auth / OTP)\n")
    rows = [
        ("makler",  "makler_mansur",  200000001, "+998901000020"),
        ("makler",  "makler_gavhar",  200000002, "+998901000021"),
        ("owner",   "owner_dilnoza",  300000001, "+998901000010"),
        ("owner",   "owner_sarvar",   300000002, "+998901000011"),
        ("student", "student_aziz",   400000001, "+998901000030"),
        ("student", "student_malika", 400000002, "+998901000031"),
        ("student", "student_jasur",  400000003, "+998901000032"),
        ("student", "student_nodira", 400000004, "+998901000033"),
    ]
    print(f"  {'Role':<10} {'Alias':<18} {'Telegram ID':<15} {'Phone'}")
    print(f"  {'-'*10} {'-'*18} {'-'*15} {'-'*18}")
    for role, alias, tid, phone in rows:
        print(f"  {role:<10} {alias:<18} {tid:<15} {phone}")
    print(f"\n  Confirmed: Successfully merged/inserted {len(users)} Users and {len(listings)} Listings with BigInteger Telegram IDs and 0 relation errors.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Aparty demo data via SQLAlchemy ORM.")
    parser.add_argument("--wipe", action="store_true", help="Wipe existing demo data before seeding.")
    args = parser.parse_args()
    asyncio.run(main(wipe=args.wipe))
