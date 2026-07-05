from __future__ import annotations

import argparse
import asyncio
import random
from dataclasses import dataclass
from itertools import cycle

import httpx


DEFAULT_BASE_URL = "http://localhost:8000/api/v1"
PASSWORD = "password123"

REGIONS: dict[str, list[str]] = {
    "Toshkent shahri": [
        "Bektemir",
        "Chilonzor",
        "Mirobod",
        "Mirzo Ulug'bek",
        "Olmazor",
        "Sergeli",
        "Shayxontohur",
        "Uchtepa",
        "Yakkasaroy",
        "Yashnobod",
        "Yunusobod",
    ],
    "Toshkent viloyati": [
        "Angren",
        "Bekobod",
        "Bo'stonliq",
        "Chinoz",
        "Chirchiq",
        "Ohangaron",
        "Olmaliq",
        "Parkent",
        "Qibray",
        "Yangiyo'l",
        "Zangiota",
    ],
    "Andijon": [
        "Andijon shahri",
        "Asaka",
        "Baliqchi",
        "Bo'ston",
        "Izboskan",
        "Marhamat",
        "Paxtaobod",
        "Qo'rg'ontepa",
        "Shahrixon",
        "Xo'jaobod",
    ],
    "Farg'ona": [
        "Farg'ona shahri",
        "Beshariq",
        "Bog'dod",
        "Dang'ara",
        "Marg'ilon",
        "Oltiariq",
        "Qo'qon",
        "Quva",
        "Rishton",
        "Toshloq",
    ],
    "Namangan": [
        "Namangan shahri",
        "Chortoq",
        "Chust",
        "Kosonsoy",
        "Mingbuloq",
        "Norin",
        "Pop",
        "To'raqo'rg'on",
        "Uchqo'rg'on",
        "Uychi",
    ],
    "Samarqand": [
        "Samarqand shahri",
        "Bulung'ur",
        "Ishtixon",
        "Jomboy",
        "Kattaqo'rg'on",
        "Narpay",
        "Pastdarg'om",
        "Payariq",
        "Toyloq",
        "Urgut",
    ],
    "Buxoro": [
        "Buxoro shahri",
        "G'ijduvon",
        "Jondor",
        "Kogon",
        "Olot",
        "Peshku",
        "Qorako'l",
        "Romitan",
        "Shofirkon",
        "Vobkent",
    ],
    "Qashqadaryo": [
        "Qarshi",
        "Chiroqchi",
        "Dehqonobod",
        "G'uzor",
        "Kitob",
        "Koson",
        "Muborak",
        "Nishon",
        "Shahrisabz",
        "Yakkabog'",
    ],
    "Surxondaryo": [
        "Termiz",
        "Angor",
        "Boysun",
        "Denov",
        "Jarqo'rg'on",
        "Qiziriq",
        "Sariosiyo",
        "Sherobod",
        "Sho'rchi",
        "Uzun",
    ],
    "Xorazm": [
        "Urganch",
        "Bog'ot",
        "Gurlan",
        "Hazorasp",
        "Xiva",
        "Xonqa",
        "Qo'shko'pir",
        "Shovot",
        "Tuproqqal'a",
        "Yangiariq",
    ],
    "Navoiy": [
        "Navoiy shahri",
        "Karmana",
        "Konimex",
        "Navbahor",
        "Nurota",
        "Qiziltepa",
        "Tomdi",
        "Uchquduq",
        "Xatirchi",
        "Zarafshon",
    ],
    "Jizzax": [
        "Jizzax shahri",
        "Arnasoy",
        "Baxmal",
        "Do'stlik",
        "Forish",
        "G'allaorol",
        "Paxtakor",
        "Sharof Rashidov",
        "Zafarobod",
        "Zomin",
    ],
    "Sirdaryo": [
        "Guliston",
        "Boyovut",
        "Mirzaobod",
        "Oqoltin",
        "Sardoba",
        "Sayxunobod",
        "Sirdaryo",
        "Xovos",
        "Yangiyer",
        "Shirin",
    ],
    "Qoraqalpog'iston": [
        "Nukus",
        "Amudaryo",
        "Beruniy",
        "Chimboy",
        "Ellikqal'a",
        "Kegeyli",
        "Mo'ynoq",
        "Qo'ng'irot",
        "Taxiatosh",
        "To'rtko'l",
    ],
}

REGION_COORDS: dict[str, tuple[float, float]] = {
    "Toshkent shahri": (41.3111, 69.2797),
    "Toshkent viloyati": (41.0275, 69.3582),
    "Andijon": (40.7821, 72.3442),
    "Farg'ona": (40.3894, 71.7864),
    "Namangan": (41.0011, 71.6726),
    "Samarqand": (39.6542, 66.9597),
    "Buxoro": (39.7747, 64.4286),
    "Qashqadaryo": (38.8610, 65.7847),
    "Surxondaryo": (37.2242, 67.2783),
    "Xorazm": (41.5500, 60.6333),
    "Navoiy": (40.1039, 65.3688),
    "Jizzax": (40.1250, 67.8808),
    "Sirdaryo": (40.4897, 68.7842),
    "Qoraqalpog'iston": (42.4619, 59.6166),
}

AMENITIES = [
    "wifi",
    "gaz",
    "suv",
    "tv",
    "konditsioner",
    "kir_mashina",
    "holodilnik",
    "oshxona_jihozi",
]

IMAGES = [
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1200&q=80",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1200&q=80",
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1200&q=80",
    "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=1200&q=80",
    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=1200&q=80",
]


@dataclass(frozen=True)
class Creator:
    user_id: int
    phone: str
    role: str
    token: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed demo listings through backend API.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--premium-ratio", type=float, default=0.2)
    parser.add_argument("--creators", type=int, default=450)
    parser.add_argument("--owner-count", type=int, default=0)
    parser.add_argument("--user-id-base", type=int, default=770000)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260509)
    return parser.parse_args()


async def request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    ok_statuses: set[int],
    **kwargs,
) -> tuple[bool, dict]:
    response = await client.request(method, url, **kwargs)
    if response.status_code in ok_statuses:
        try:
            return True, response.json()
        except ValueError:
            return True, {}
    try:
        data = response.json()
    except ValueError:
        data = {"detail": response.text}
    return False, {"status_code": response.status_code, **data}


async def ensure_user(client: httpx.AsyncClient, user_id: int, role_id: int, role: str) -> str:
    phone = f"+99877{user_id}"
    payload = {
        "user_id": user_id,
        "full_name": f"Demo {role.title()} {user_id}",
        "phone": phone,
        "role_id": role_id,
        "password": PASSWORD,
    }
    ok, data = await request_json(client, "POST", "/auth/register", ok_statuses={201, 400}, json=payload)
    if not ok:
        raise RuntimeError(f"register failed for {phone}: {data}")
    if data.get("detail") and "allaqachon" not in str(data["detail"]):
        raise RuntimeError(f"register rejected for {phone}: {data}")
    return phone


async def login(client: httpx.AsyncClient, phone: str) -> str:
    ok, data = await request_json(
        client,
        "POST",
        "/auth/login",
        ok_statuses={200},
        json={"phone": phone, "password": PASSWORD},
    )
    if not ok:
        raise RuntimeError(f"login failed for {phone}: {data}")
    return data["access_token"]


async def prepare_one_creator(
    client: httpx.AsyncClient,
    user_id: int,
    role_id: int,
    role: str,
    semaphore: asyncio.Semaphore,
) -> Creator:
    async with semaphore:
        phone = await ensure_user(client, user_id, role_id, role)
        token = await login(client, phone)
        return Creator(user_id=user_id, phone=phone, role=role, token=token)


async def prepare_creators_for_args(client: httpx.AsyncClient, args: argparse.Namespace) -> list[Creator]:
    creators: list[Creator] = []
    owner_count = max(min(args.owner_count, args.creators), 0)
    makler_count = max(args.creators - owner_count, 1)
    jobs = []

    for index in range(makler_count):
        user_id = args.user_id_base + index
        jobs.append((user_id, 3, "makler"))
    for index in range(owner_count):
        user_id = args.user_id_base + makler_count + index
        jobs.append((user_id, 2, "owner"))

    semaphore = asyncio.Semaphore(args.concurrency)
    tasks = [
        asyncio.create_task(prepare_one_creator(client, user_id, role_id, role, semaphore))
        for user_id, role_id, role in jobs
    ]
    for number, task in enumerate(asyncio.as_completed(tasks), start=1):
        creators.append(await task)
        if number % 50 == 0 or number == len(jobs):
            print(f"Creators ready: {number}/{len(jobs)}", flush=True)

    return creators


def listing_payload(index: int, is_premium: bool, region: str, district: str) -> dict:
    rooms = random.randint(1, 5)
    max_occupants = random.randint(max(rooms, 1), max(rooms + 3, 3))
    available_spaces = random.randint(1, max_occupants)
    price_base = random.randint(80, 260) if rooms == 1 else random.randint(220, 900)
    image_start = index % len(IMAGES)
    images = [IMAGES[image_start], IMAGES[(image_start + 1) % len(IMAGES)]]
    amenities = {name: random.random() < 0.68 for name in AMENITIES}
    if is_premium:
        amenities.update({"wifi": True, "suv": True, "gaz": True, "oshxona_jihozi": True})
    center_lat, center_lng = REGION_COORDS.get(region, REGION_COORDS["Andijon"])

    return {
        "viloyat": region,
        "tuman": district,
        "manzil": f"Demo ko'cha {index % 120 + 1}, {district}",
        "dom_raqami": str(index % 80 + 1),
        "xona_raqami": str(index % 45 + 1),
        "qavat": random.randint(1, 9),
        "jami_qavat": random.randint(9, 16),
        "latitude": round(center_lat + random.uniform(-0.08, 0.08), 6),
        "longitude": round(center_lng + random.uniform(-0.08, 0.08), 6),
        "xonalar_soni": rooms,
        "maydon_m2": random.randint(28, 120),
        "narx_usd": price_base + (70 if is_premium else 0),
        "jins": random.choice(["male", "female", "mixed"]),
        "max_kishi": max_occupants,
        "bosh_joy": available_spaces,
        "qulayliklar": amenities,
        "rasmlar": images,
        "tavsif": (
            f"{region}, {district} bo'yicha demo "
            f"{'premium' if is_premium else 'oddiy'} e'lon. "
            "Talabalar va ijarachilar uchun qulay joylashuv."
        ),
        "premium": is_premium,
    }


async def create_listing(
    client: httpx.AsyncClient,
    creator: Creator,
    payload: dict,
    semaphore: asyncio.Semaphore,
) -> tuple[bool, dict]:
    async with semaphore:
        return await request_json(
            client,
            "POST",
            "/listings/",
            ok_statuses={201},
            json=payload,
            headers={"Authorization": f"Bearer {creator.token}"},
        )


async def seed_listings(client: httpx.AsyncClient, args: argparse.Namespace, creators: list[Creator]) -> None:
    premium_target = int(args.count * args.premium_ratio)
    region_district_pairs = [
        (region, district)
        for region, districts in REGIONS.items()
        for district in districts
    ]
    pair_cycle = cycle(region_district_pairs)
    creator_cycle = cycle(creators)
    semaphore = asyncio.Semaphore(args.concurrency)
    created = 0
    premium_created = 0
    failed = 0

    pending: list[asyncio.Task] = []
    for index in range(args.count):
        region, district = next(pair_cycle)
        is_premium = premium_created < premium_target
        creator = next(creator_cycle)
        payload = listing_payload(index + 1, is_premium, region, district)
        pending.append(asyncio.create_task(create_listing(client, creator, payload, semaphore)))
        if is_premium:
            premium_created += 1

        if len(pending) >= args.concurrency * 4:
            for task in asyncio.as_completed(pending):
                ok, data = await task
                if ok:
                    created += 1
                else:
                    failed += 1
                    print(f"Create failed: {data}")
            pending.clear()
            print(f"Progress: {created}/{args.count} created, {failed} failed", flush=True)

    for task in asyncio.as_completed(pending):
        ok, data = await task
        if ok:
            created += 1
        else:
            failed += 1
            print(f"Create failed: {data}")

    print(f"Done: {created} listings created, {failed} failed, premium planned: {premium_target}", flush=True)


async def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    limits = httpx.Limits(max_connections=args.concurrency * 2, max_keepalive_connections=args.concurrency)
    async with httpx.AsyncClient(base_url=args.base_url, timeout=30.0, limits=limits) as client:
        health = await client.get("/health")
        health.raise_for_status()
        print(f"Backend OK: {args.base_url}", flush=True)
        creators = await prepare_creators_for_args(client, args)
        print(f"Total creators ready: {len(creators)}", flush=True)
        await seed_listings(client, args, creators)


if __name__ == "__main__":
    asyncio.run(main())
