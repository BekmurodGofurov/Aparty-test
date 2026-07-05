import os
import asyncio
import re
import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, select
from app.models.listing import Listing, ListingSource
from app.config import settings
from app.services.location_service import KnownPlace, distance_km, find_known_place
from typing import List, Optional, Dict, Any

AMENITY_ALIASES = {
    "ac": "konditsioner",
    "conditioner": "konditsioner",
    "konditsioner": "konditsioner",
    "kondisioner": "konditsioner",
    "wifi": "wifi",
    "wi-fi": "wifi",
}

# Configure Gemini
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)


def normalize_amenities(amenities: Optional[List[str]] = None) -> List[str]:
    normalized = []
    for amenity in amenities or []:
        key = AMENITY_ALIASES.get(str(amenity).strip().lower())
        if key and key not in normalized:
            normalized.append(key)
    return normalized


def format_listing_results(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "Kechirasiz, hozirda bazamizda bunday uylar mavjud emas, lekin tez orada qo'shilishi mumkin."

    lines = ["Sizga mos kelishi mumkin bo'lgan uylar:"]
    for index, listing in enumerate(results, start=1):
        amenities = listing.get("amenities") or []
        amenities_text = f" Qulayliklar: {', '.join(amenities)}." if amenities else ""
        distance_text = f" {listing['distance_text']}." if listing.get("distance_text") else ""
        source_text = " Roommate/bo'sh joy e'loni." if listing.get("is_roommate_listing") else ""
        lines.append(
            f"{index}. {listing['price']} - {listing['address']}. "
            f"{listing['rooms']} xona, {listing['gender']}.{distance_text}{source_text}{amenities_text}"
        )
    return "\n".join(lines)


def format_search_summary(results: List[Dict[str, Any]], args: Dict[str, Any]) -> str:
    if not results:
        return "Kechirasiz, hozircha bu shartlarga mos kvartira topilmadi."

    if args.get("joy_nomi") or args.get("near_place"):
        place_name = args.get("resolved_place_name") or args.get("joy_nomi") or args.get("near_place")
        roommate_text = " roommate/bo'sh joy e'lonlari orasidan" if args.get("roommate") else ""
        return (
            f"{place_name} yaqinidan{roommate_text} {len(results)} ta mos variant topdim. "
            "Eng yaqinlari birinchi chiqdi."
        )

    place = ", ".join(
        str(value)
        for value in (args.get("viloyat"), args.get("tuman"))
        if value
    )
    price_parts = []
    if args.get("min_narx"):
        price_parts.append(f"{int(args['min_narx'])}$ dan")
    if args.get("max_narx"):
        price_parts.append(f"{int(args['max_narx'])}$ gacha")
    price_text = " ".join(price_parts)

    details = ", ".join(part for part in (place, price_text) if part)
    if details:
        return f"{details} bo'yicha {len(results)} ta mos variant topdim. Kartani bosib, e'lon ichiga kirishingiz mumkin."
    return f"{len(results)} ta mos variant topdim. Kartani bosib, e'lon ichiga kirishingiz mumkin."

async def search_listings_db(
    db: AsyncSession,
    region: Optional[str] = None,
    district: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    rooms: Optional[int] = None,
    gender: Optional[str] = None,
    amenities: Optional[List[str]] = None,
    near_place: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None,
    roommate: bool = False,
    resolved_place_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search listings from database
    """
    resolved_place = find_known_place(near_place or "")
    if resolved_place and (latitude is None or longitude is None):
        latitude = resolved_place.latitude
        longitude = resolved_place.longitude
        region = region or resolved_place.region

    query = select(Listing).where(Listing.is_active == True)
    
    if region:
        query = query.where(Listing.region.ilike(f"%{region}%"))
    if district:
        query = query.where(Listing.district.ilike(f"%{district}%"))
    if min_price:
        query = query.where(Listing.price_usd >= min_price)
    if max_price:
        query = query.where(Listing.price_usd <= max_price)
    if rooms:
        query = query.where(Listing.rooms_count == rooms)
    if gender:
        query = query.where(Listing.target_gender == gender)
    requested_amenities = normalize_amenities(amenities)
    for amenity in requested_amenities:
        query = query.where(Listing.amenities[amenity].as_boolean() == True)

    if roommate:
        query = query.where(Listing.available_spaces >= 1)
        query = query.where(
            (Listing.source == ListingSource.exiting_student)
            | (Listing.max_occupants > 1)
        )

    query = query.order_by(desc(Listing.is_premium), desc(Listing.created_at)).limit(500 if latitude and longitude else 5)
    result = await db.execute(query)
    listings = list(result.scalars().all())

    origin: Optional[KnownPlace | Dict[str, Any]] = resolved_place
    if latitude is not None and longitude is not None:
        effective_radius = float(radius_km or (5 if roommate else 8))
        enriched = []
        for listing in listings:
            km = distance_km(float(latitude), float(longitude), listing.latitude, listing.longitude)
            if km <= effective_radius:
                enriched.append((listing, km))
        enriched.sort(key=lambda item: (item[1], item[0].price_usd))
        listings_with_distance = enriched[:5]
    else:
        listings_with_distance = [(listing, None) for listing in listings[:5]]
    
    return [
        {
            "id": str(l.id),
            "url": f"/listing/{l.id}",
            "address": f"{l.region}, {l.district}, {l.address or ''}",
            "price": f"{l.price_usd}$",
            "price_usd": l.price_usd,
            "region": l.region,
            "district": l.district,
            "rooms": l.rooms_count,
            "gender": l.target_gender,
            "source": l.source,
            "available_spaces": l.available_spaces,
            "max_occupants": l.max_occupants,
            "is_roommate_listing": l.source == ListingSource.exiting_student,
            "distance_km": round(km, 2) if km is not None else None,
            "distance_text": f"{km:.1f} km uzoqlikda" if km is not None else None,
            "near_place": origin.name if isinstance(origin, KnownPlace) else None,
            "amenities": [
                key for key, enabled in (l.amenities or {}).items()
                if enabled and key in {"wifi", "konditsioner", "gaz", "suv", "tv"}
            ],
            "image": l.images[0] if l.images else None,
            "description": l.description[:150] + "..." if l.description and len(l.description) > 150 else l.description or ""
        }
        for l, km in listings_with_distance
    ]


async def search_listings_db_uz(
    db: AsyncSession,
    viloyat: Optional[str] = None,
    tuman: Optional[str] = None,
    min_narx: Optional[int] = None,
    max_narx: Optional[int] = None,
    xonalar: Optional[int] = None,
    jins: Optional[str] = None,
    qulayliklar: Optional[List[str]] = None,
    joy_nomi: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None,
    roommate: bool = False,
    resolved_place_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    gender_map = {"erkak": "male", "ayol": "female", "aralash": "mixed"}
    return await search_listings_db(
        db=db,
        region=viloyat,
        district=tuman,
        min_price=int(min_narx) if min_narx else None,
        max_price=int(max_narx) if max_narx else None,
        rooms=xonalar,
        gender=gender_map.get(jins, jins),
        amenities=qulayliklar,
        near_place=joy_nomi,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        roommate=roommate,
    )


def parse_direct_search_request(message: str) -> Optional[Dict[str, Any]]:
    text = (message or "").lower()
    if not text.strip():
        return None

    place = find_known_place(text)
    search_words = (
        "kvartira",
        "kvarita",
        "uy",
        "ijara",
        "xona",
        "joy",
        "roommate",
        "qoshil",
        "qo'shil",
        "sherik",
        "yonidan",
        "yaqin",
    )
    if not place and not any(word in text for word in search_words):
        return None

    args: Dict[str, Any] = {}
    if place:
        args.update(
            {
                "joy_nomi": place.name,
                "viloyat": place.region,
                "radius_km": 6,
                "resolved_place_name": place.name,
            }
        )

    price_match = re.search(r"(\d{2,5})\s*(?:\$|dollar|usd)", text)
    if price_match and any(word in text for word in ("gacha", "max", "arzon", "ostida")):
        args["max_narx"] = int(price_match.group(1))
    elif price_match and any(word in text for word in ("dan", "min")):
        args["min_narx"] = int(price_match.group(1))

    room_match = re.search(r"(\d+)\s*(?:xona|xonali|kishilik|kishi)", text)
    if room_match and "kishi" not in room_match.group(0):
        args["xonalar"] = int(room_match.group(1))

    if any(word in text for word in ("erkak", "yigit", "bola")):
        args["jins"] = "erkak"
    elif any(word in text for word in ("ayol", "qiz")):
        args["jins"] = "ayol"

    if any(word in text for word in ("roommate", "sherik", "qoshil", "qo'shil", "bir kishiman", "1 kishiman", "bo'sh joy", "bosh joy")):
        args["roommate"] = True
        args.setdefault("radius_km", 8)

    amenities = []
    for requested, normalized in (("wifi", "wifi"), ("wi-fi", "wifi"), ("konditsioner", "konditsioner"), ("ac", "konditsioner")):
        if requested in text and normalized not in amenities:
            amenities.append(normalized)
    if amenities:
        args["qulayliklar"] = amenities

    return args or None

# AI System Prompt
SYSTEM_PROMPT = """
Siz Aparty.uz platformasining rasmiy va aqlli yordamchisisiz. 

ASOSIY VAZIFANGIZ:
Foydalanuvchilarga ijara uylarini topishda yordam berish.

QOIDALAR:
1. FOYDALANUVCHI UY QIDIRSA: Har qanday uy qidirish bilan bog'liq so'rovda (masalan: "Andijondan uy kerak", "300 dollargacha uylar", "2 xonali kvartiralar", "Sharda yonidan kvartira") ALBATTA `search_listings_db` funksiyasini chaqiring.
2. QIDIRUV PARAMETRLARI: Foydalanuvchi aytgan viloyat, tuman, narx, xonalar soni, joy nomi/universitet/landmark va qulayliklarni aniq ajratib oling va funksiyaga bering. "wifi", "wi-fi" va "ac" so'zlarini qulayliklar sifatida yuboring.
3. JAVOB BERISH: Funksiyadan kelgan natijalar asosida foydalanuvchiga chiroyli ro'yxat ko'rinishida javob bering. Har bir uyning narxi, manzili va qisqacha tavsifini ko'rsating.
4. JOY NOMI: Agar foydalanuvchi universitet, institut, savdo markazi yoki landmark nomini aytsa, uni `joy_nomi` sifatida yuboring. Masalan, "Sharda university yonidan" -> joy_nomi="Sharda University Uzbekistan".
5. ROOMMATE: Agar foydalanuvchi "roommate", "sherik", "kimlargadir qo'shilaman", "bir kishiman", "bo'sh joy kerak" desa, `roommate=true` yuboring.
6. AGAR UY TOPILMASA: "Kechirasiz, hozirda bazamizda bunday uylar mavjud emas, lekin tez orada qo'shilishi mumkin" deb javob bering.
7. MULOQOT: Faqat o'zbek tilida gapiring. Juda xushmuomala bo'ling.
8. FORMAT: Markdown formatidan foydalaning.
"""

class AIService:
    def __init__(self):
        self.model_name = "models/gemini-2.5-flash"
        self._initialized = False
        self.model = None
        self.tools = [
            {
                "function_declarations": [
                    {
                        "name": "search_listings_db",
                        "description": "Uylarni viloyat, tuman, narx, xonalar soni, joy nomiga yaqinlik va roommate/bo'sh joy e'lonlari bo'yicha qidiradi.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "viloyat": {"type": "string", "description": "Viloyat nomi"},
                                "tuman": {"type": "string", "description": "Tuman nomi"},
                                "min_narx": {"type": "integer", "description": "Minimal narx ($)"},
                                "max_narx": {"type": "integer", "description": "Maximal narx ($)"},
                                "xonalar": {"type": "integer", "description": "Xonalar soni"},
                                "jins": {"type": "string", "description": "Kim uchun (erkak, ayol, aralash)"},
                                "joy_nomi": {"type": "string", "description": "Universitet, institut, landmark yoki aniq joy nomi. Masalan: Sharda University Uzbekistan"},
                                "latitude": {"type": "number", "description": "Joy nomi koordinatasi latitude qiymati, agar ma'lum bo'lsa"},
                                "longitude": {"type": "number", "description": "Joy nomi koordinatasi longitude qiymati, agar ma'lum bo'lsa"},
                                "radius_km": {"type": "number", "description": "Joy nomi atrofida necha km radiusda qidirish"},
                                "roommate": {"type": "boolean", "description": "Roommate, sherik yoki mavjud ijarachilarga qo'shilish e'lonlarini qidirish"},
                                "qulayliklar": {
                                    "type": "array",
                                    "description": "Kerakli qulayliklar, masalan: wifi, ac, konditsioner",
                                    "items": {"type": "string"}
                                }
                            }
                        }
                    }
                ]
            }
        ]

    def _ensure_initialized(self):
        if self._initialized:
            return
            
        api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("DEBUG: API Key TOPILMADI!")
            return

        genai.configure(api_key=api_key)
        try:
            self.model_name = self._select_model_name()
            print(f"DEBUG: Tanlangan model: {self.model_name}")
            
            # Tools definition
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
                tools=self.tools
            )
            self._initialized = True
        except Exception as e:
            print(f"DEBUG: Model yuklashda xato: {str(e)}")

    def _select_model_name(self) -> str:
        preferred_models = (
            "models/gemini-2.5-flash",
            "models/gemini-flash-latest",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-001",
            "models/gemini-2.0-flash-lite",
        )

        try:
            available_models = {
                model.name
                for model in genai.list_models()
                if "generateContent" in getattr(model, "supported_generation_methods", [])
            }
        except Exception as e:
            print(f"DEBUG: Model ro'yxatini olishda xato: {str(e)}")
            return preferred_models[0]

        for model_name in preferred_models:
            if model_name in available_models:
                return model_name

        if available_models:
            return sorted(available_models)[0]

        return preferred_models[0]

    async def chat(self, user_message: str, db: AsyncSession, history: List = None) -> Dict[str, Any]:
        direct_args = parse_direct_search_request(user_message)
        if direct_args:
            try:
                results = await search_listings_db_uz(db, **direct_args)
            except (TimeoutError, OSError, SQLAlchemyError) as e:
                print(f"DEBUG: AI DB qidiruv xatosi: {e}")
                return {
                    "text": "Kechirasiz, hozir qidiruv bazasi bilan aloqa vaqtincha ishlamayapti. Bir ozdan keyin qayta urinib ko'ring.",
                    "listings": [],
                }
            return {
                "text": format_search_summary(results, direct_args),
                "listings": results,
            }

        self._ensure_initialized()
        
        if not self.model:
            return {"text": "Kechirasiz, AI xizmati sozlanmagan. API Keyni tekshiring.", "listings": []}
            
        print(f"DEBUG: Chat xabari yuborilmoqda: {user_message}")
        
        try:
            return await self._chat_with_model_safe(self.model, user_message, db, history)
        except Exception as e:
            error_msg = str(e)
            print(f"DEBUG AI Xatosi: {error_msg}")
            
            if "429" in error_msg or "resource_exhausted" in error_msg.lower():
                return {
                    "text": "Kechirasiz, hozirda so'rovlar soni ko'payib ketdi. Iltimos, bir ozdan so'ng qayta urinib ko'ring (AI limitga yetdi).",
                    "listings": [],
                }
            
            return {"text": f"Kechirasiz, xatolik yuz berdi: {error_msg}", "listings": []}

    async def _chat_with_model_safe(self, model, user_message: str, db: AsyncSession, history: List = None) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        chat = model.start_chat(history=history or [])
        
        print(f"DEBUG: Gemini ga so'rov ketmoqda...")
        response = await loop.run_in_executor(None, lambda: chat.send_message(user_message))
        print(f"DEBUG: Gemini dan javob keldi.")
        
        # Check for function calls
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    fn_name = part.function_call.name
                    fn_args = part.function_call.args
                    print(f"DEBUG: AI funksiya chaqirdi: {fn_name} | Argumentlar: {fn_args}")
                    
                    if fn_name == "search_listings_db":
                        # Convert to dict for unpack
                        args = {}
                        for key, val in fn_args.items():
                            args[key] = val
                            
                        print(f"DEBUG: Bazadan qidirilmoqda: {args}")
                        try:
                            results = await search_listings_db_uz(db, **args)
                        except (TimeoutError, OSError, SQLAlchemyError) as e:
                            print(f"DEBUG: AI DB qidiruv xatosi: {e}")
                            return {
                                "text": "Kechirasiz, hozir qidiruv bazasi bilan aloqa vaqtincha ishlamayapti. Bir ozdan keyin qayta urinib ko'ring.",
                                "listings": [],
                            }
                        print(f"DEBUG: Baza natijalari: {len(results)} ta topildi")
                        return {
                            "text": format_search_summary(results, args),
                            "listings": results,
                        }
        
        return {"text": response.text, "listings": []}

ai_service = AIService()
