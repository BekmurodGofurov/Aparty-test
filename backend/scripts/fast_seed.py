import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from app.database import engine

# Demo data constants
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
    "Jizzax": ["Jizzax shahar", "Zomin", "G'allaorol", "Paxtakor"]
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

AMENITIES_LIST = ["wifi", "gaz", "suv", "tv", "konditsioner", "kir_mashina", "holodilnik", "oshxona_jihozi"]

async def seed():
    async with engine.begin() as conn:
        print("Cleaning up old demo data...")
        # Optional: clear existing data if desired, but here we just append
        
        print("Creating users...")
        # Roles: 1:student, 2:owner, 3:makler, 4:admin
        # Password hash for 'password123'
        pwd_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6L2GdgGbgCl6.uXG" 
        
        # Admins
        for i in range(5):
            await conn.execute(text("""
                INSERT INTO users (user_id, full_name, phone, role_id, password_hash, verified)
                VALUES (:uid, :name, :phone, 4, :pwd, true)
                ON CONFLICT (user_id) DO NOTHING
            """), {"uid": 1000+i, "name": f"Admin {i+1}", "phone": f"+99890111000{i}", "pwd": pwd_hash})
            
        # Brokers (100)
        broker_ids = []
        for i in range(100):
            uid = 2000+i
            broker_ids.append(uid)
            await conn.execute(text("""
                INSERT INTO users (user_id, full_name, phone, role_id, password_hash, verified)
                VALUES (:uid, :name, :phone, 3, :pwd, true)
                ON CONFLICT (user_id) DO NOTHING
            """), {"uid": uid, "name": f"Broker {i+1}", "phone": f"+9989022200{i:02d}", "pwd": pwd_hash})
            
        # Owners (30)
        owner_ids = []
        for i in range(30):
            uid = 3000+i
            owner_ids.append(uid)
            await conn.execute(text("""
                INSERT INTO users (user_id, full_name, phone, role_id, password_hash, verified)
                VALUES (:uid, :name, :phone, 2, :pwd, true)
                ON CONFLICT (user_id) DO NOTHING
            """), {"uid": uid, "name": f"Owner {i+1}", "phone": f"+9989033300{i:02d}", "pwd": pwd_hash})
            
        # Students (70)
        for i in range(70):
            await conn.execute(text("""
                INSERT INTO users (user_id, full_name, phone, role_id, password_hash, verified)
                VALUES (:uid, :name, :phone, 1, :pwd, true)
                ON CONFLICT (user_id) DO NOTHING
            """), {"uid": 4000+i, "name": f"Student {i+1}", "phone": f"+9989044400{i:02d}", "pwd": pwd_hash})

        print("Creating 2000 listings...")
        creators = broker_ids + owner_ids
        now = datetime.now(timezone.utc)
        
        for i in range(2000):
            lid = uuid.uuid4()
            region = random.choice(list(REGIONS.keys()))
            district = random.choice(REGIONS[region])
            center_lat, center_lon = REGION_COORDS.get(region, (40.7821, 72.3442))
            owner_id = random.choice(creators)
            is_premium = i < 200 # First 200 are premium
            expires = now + timedelta(days=30) if is_premium else None
            
            amenities = {a: random.choice([True, False]) for a in AMENITIES_LIST}
            images = ["https://picsum.photos/800/600", "https://picsum.photos/801/601"]
            
            await conn.execute(text("""
                INSERT INTO listings (id, owner_id, region, district, address, latitude, longitude, 
                                     rooms_count, price_usd, target_gender, source, max_occupants, 
                                     available_spaces, amenities, images, description, is_premium, 
                                     premium_expires_at, is_active, view_count, created_at)
                VALUES (:id, :oid, :reg, :dist, :addr, :lat, :lon, :rooms, :price, :gen, :src, :max_occ, 
                        :avail, CAST(:amen AS JSON), :imgs, :desc, :prem, :exp, true, :views, :cat)
            """), {
                "id": lid, "oid": owner_id, "reg": region, "dist": district, "addr": f"Ko'cha {i}",
                "lat": center_lat + random.uniform(-0.08, 0.08), "lon": center_lon + random.uniform(-0.08, 0.08),
                "rooms": random.randint(1, 5), "price": random.randint(200, 2000), 
                "gen": random.choice(["male", "female", "mixed"]), 
                "src": "makler" if owner_id in broker_ids else "owner",
                "max_occ": 4, "avail": random.randint(1, 4), "amen": json.dumps(amenities),
                "imgs": images, "desc": "Demo listing", "prem": is_premium, "views": random.randint(20, 2500),
                "exp": expires, "cat": now
            })
            
            if (i + 1) % 500 == 0:
                print(f"Inserted {i+1} listings...")

    print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
