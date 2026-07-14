"""
AI Service — powered by Groq (llama3-70b-8192).

Architecture (Clean Architecture, unchanged from previous Gemini version):
  - Pure utility functions (no I/O): normalize_amenities, format_*, parse_*
  - search_listings_db / search_listings_db_uz  – pure DB queries
  - AIService class          – orchestrates LLM + DB
  - ai_service singleton     – imported by the router
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from groq import AsyncGroq
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.listing import Listing, ListingSource
from app.services.location_service import KnownPlace, distance_km, find_known_place

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GROQ_MODEL = "llama3-70b-8192"

AMENITY_ALIASES: Dict[str, str] = {
    "ac": "ac",
    "conditioner": "ac",
    "konditsioner": "ac",
    "kondisioner": "ac",
    "air_conditioning": "ac",
    "wifi": "wifi",
    "wi-fi": "wifi",
    "gas": "gas",
    "gaz": "gas",
    "water": "water",
    "suv": "water",
    "tv": "tv",
    "washer": "washer",
    "kir_mashina": "washer",
    "kir mashina": "washer",
    "washing_machine": "washer",
    "fridge": "fridge",
    "holodilnik": "fridge",
    "refrigerator": "fridge",
    "sovutkich": "fridge",
    "kitchenware": "kitchenware",
    "oshxona_jihozi": "kitchenware",
    "kitchen_appliances": "kitchenware",
}

# Tool schema — identical semantics to the old Gemini function declaration.
_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_listings_db",
            "description": (
                "Uylarni viloyat, tuman, narx, xonalar soni, joy nomiga yaqinlik "
                "va roommate/bo'sh joy e'lonlari bo'yicha qidiradi."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "viloyat": {"type": "string", "description": "Viloyat nomi"},
                    "tuman": {"type": "string", "description": "Tuman nomi"},
                    "min_narx": {"type": "integer", "description": "Minimal narx ($)"},
                    "max_narx": {"type": "integer", "description": "Maximal narx ($)"},
                    "xonalar": {"type": "integer", "description": "Xonalar soni"},
                    "jins": {
                        "type": "string",
                        "description": "Kim uchun (erkak, ayol, aralash)",
                    },
                    "joy_nomi": {
                        "type": "string",
                        "description": (
                            "Universitet, institut, landmark yoki aniq joy nomi. "
                            "Masalan: Sharda University Uzbekistan"
                        ),
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Joy nomi koordinatasi latitude qiymati, agar ma'lum bo'lsa",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Joy nomi koordinatasi longitude qiymati, agar ma'lum bo'lsa",
                    },
                    "radius_km": {
                        "type": "number",
                        "description": "Joy nomi atrofida necha km radiusda qidirish",
                    },
                    "roommate": {
                        "type": "boolean",
                        "description": "Roommate, sherik yoki mavjud ijarachilarga qo'shilish e'lonlarini qidirish",
                    },
                    "qulayliklar": {
                        "type": "array",
                        "description": "Kerakli qulayliklar, masalan: wifi, ac, konditsioner",
                        "items": {"type": "string"},
                    },
                },
            },
        },
    }
]

# System prompt (unchanged semantics, provider-agnostic text).
SYSTEM_PROMPT = """\
Siz Aparty.uz platformasining rasmiy va aqlli yordamchisisiz.

ASOSIY VAZIFANGIZ:
Foydalanuvchilarga ijara uylarini topishda yordam berish.

QOIDALAR:
1. FOYDALANUVCHI UY QIDIRSA: Har qanday uy qidirish bilan bog'liq so'rovda \
(masalan: "Andijondan uy kerak", "300 dollargacha uylar", "2 xonali kvartiralar", \
"Sharda yonidan kvartira") ALBATTA `search_listings_db` funksiyasini chaqiring.
2. QIDIRUV PARAMETRLARI: Foydalanuvchi aytgan viloyat, tuman, narx, xonalar soni, \
joy nomi/universitet/landmark va qulayliklarni aniq ajratib oling va funksiyaga bering. \
"wifi", "wi-fi" va "ac" so'zlarini qulayliklar sifatida yuboring.
3. JAVOB BERISH: Funksiyadan kelgan natijalar asosida foydalanuvchiga chiroyli \
ro'yxat ko'rinishida javob bering. Har bir uyning narxi, manzili va qisqacha tavsifini ko'rsating.
4. JOY NOMI: Agar foydalanuvchi universitet, institut, savdo markazi yoki landmark nomini aytsa, \
uni `joy_nomi` sifatida yuboring. Masalan, "Sharda university yonidan" -> joy_nomi="Sharda University Uzbekistan".
5. ROOMMATE: Agar foydalanuvchi "roommate", "sherik", "kimlargadir qo'shilaman", \
"bir kishiman", "bo'sh joy kerak" desa, `roommate=true` yuboring.
6. AGAR UY TOPILMASA: "Kechirasiz, hozirda bazamizda bunday uylar mavjud emas, \
lekin tez orada qo'shilishi mumkin" deb javob bering.
7. MULOQOT: Faqat o'zbek tilida gapiring. Juda xushmuomala bo'ling.
8. FORMAT: Markdown formatidan foydalaning.
"""


# ---------------------------------------------------------------------------
# Pure utility helpers (no external I/O)
# ---------------------------------------------------------------------------


def normalize_amenities(amenities: Optional[List[str]] = None) -> List[str]:
    normalized: List[str] = []
    for amenity in amenities or []:
        key = AMENITY_ALIASES.get(str(amenity).strip().lower())
        if key and key not in normalized:
            normalized.append(key)
    return normalized


def format_listing_results(results: List[Dict[str, Any]]) -> str:
    if not results:
        return (
            "Kechirasiz, hozirda bazamizda bunday uylar mavjud emas, "
            "lekin tez orada qo'shilishi mumkin."
        )

    lines = ["Sizga mos kelishi mumkin bo'lgan uylar:"]
    for index, listing in enumerate(results, start=1):
        amenities = listing.get("amenities") or []
        amenities_text = f" Qulayliklar: {', '.join(amenities)}." if amenities else ""
        distance_text = (
            f" {listing['distance_text']}." if listing.get("distance_text") else ""
        )
        source_text = (
            " Roommate/bo'sh joy e'loni." if listing.get("is_roommate_listing") else ""
        )
        lines.append(
            f"{index}. {listing['price']} - {listing['address']}. "
            f"{listing['rooms']} xona, {listing['gender']}."
            f"{distance_text}{source_text}{amenities_text}"
        )
    return "\n".join(lines)


def format_search_summary(results: List[Dict[str, Any]], args: Dict[str, Any]) -> str:
    if not results:
        return "Kechirasiz, hozircha bu shartlarga mos kvartira topilmadi."

    if args.get("joy_nomi") or args.get("near_place"):
        place_name = (
            args.get("resolved_place_name")
            or args.get("joy_nomi")
            or args.get("near_place")
        )
        roommate_text = (
            " roommate/bo'sh joy e'lonlari orasidan" if args.get("roommate") else ""
        )
        return (
            f"{place_name} yaqinidan{roommate_text} {len(results)} ta mos variant topdim. "
            "Eng yaqinlari birinchi chiqdi."
        )

    place = ", ".join(
        str(value)
        for value in (args.get("viloyat"), args.get("tuman"))
        if value
    )
    price_parts: List[str] = []
    if args.get("min_narx"):
        price_parts.append(f"{int(args['min_narx'])}$ dan")
    if args.get("max_narx"):
        price_parts.append(f"{int(args['max_narx'])}$ gacha")
    price_text = " ".join(price_parts)

    details = ", ".join(part for part in (place, price_text) if part)
    if details:
        return (
            f"{details} bo'yicha {len(results)} ta mos variant topdim. "
            "Kartani bosib, e'lon ichiga kirishingiz mumkin."
        )
    return f"{len(results)} ta mos variant topdim. Kartani bosib, e'lon ichiga kirishingiz mumkin."


def parse_direct_search_request(message: str) -> Optional[Dict[str, Any]]:
    """
    Fast, zero-LLM path: parse a simple Uzbek query directly with regex.
    Returns extracted args dict or None if the message doesn't look like a search.
    """
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
        args["jins"] = "male"
    elif any(word in text for word in ("ayol", "qiz")):
        args["jins"] = "female"

    if any(
        word in text
        for word in (
            "roommate",
            "sherik",
            "qoshil",
            "qo'shil",
            "bir kishiman",
            "1 kishiman",
            "bo'sh joy",
            "bosh joy",
        )
    ):
        args["roommate"] = True
        args.setdefault("radius_km", 8)

    amenities: List[str] = []
    for requested, normalized in (
        ("wifi", "wifi"),
        ("wi-fi", "wifi"),
        ("konditsioner", "ac"),
        ("ac", "ac"),
        ("kir mashina", "washer"),
        ("kir_mashina", "washer"),
        ("washer", "washer"),
        ("holodilnik", "fridge"),
        ("fridge", "fridge"),
        ("oshxona jihozi", "kitchenware"),
        ("kitchenware", "kitchenware"),
        ("gaz", "gas"),
        ("gas", "gas"),
        ("suv", "water"),
        ("water", "water"),
    ):
        if requested in text and normalized not in amenities:
            amenities.append(normalized)
    if amenities:
        args["qulayliklar"] = amenities

    return args or None


# ---------------------------------------------------------------------------
# Database search helpers
# ---------------------------------------------------------------------------


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
    """Search listings from the database and return enriched dicts."""
    resolved_place = find_known_place(near_place or "")
    if resolved_place and (latitude is None or longitude is None):
        latitude = resolved_place.latitude
        longitude = resolved_place.longitude
        region = region or resolved_place.region

    query = select(Listing).where(Listing.is_active == True)  # noqa: E712

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
        query = query.where(Listing.amenities[amenity].as_boolean() == True)  # noqa: E712

    if roommate:
        query = query.where(Listing.available_spaces >= 1)
        query = query.where(
            (Listing.source == ListingSource.exiting_student)
            | (Listing.max_occupants > 1)
        )

    limit = 500 if (latitude and longitude) else 5
    query = query.order_by(desc(Listing.is_premium), desc(Listing.created_at)).limit(limit)

    result = await db.execute(query)
    listings = list(result.scalars().all())

    origin: Optional[KnownPlace | Dict[str, Any]] = resolved_place
    if latitude is not None and longitude is not None:
        effective_radius = float(radius_km or (5 if roommate else 8))
        enriched = []
        for listing in listings:
            km = distance_km(
                float(latitude), float(longitude), listing.latitude, listing.longitude
            )
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
                key
                for key, enabled in (l.amenities or {}).items()
                if enabled and key in {"wifi", "ac", "gas", "water", "tv", "washer", "fridge", "kitchenware"}
            ],
            "image": l.images[0] if l.images else None,
            "description": (
                l.description[:150] + "..."
                if l.description and len(l.description) > 150
                else l.description or ""
            ),
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


# ---------------------------------------------------------------------------
# AIService — Groq-backed implementation
# ---------------------------------------------------------------------------


class AIService:
    """
    Async AI service that uses the Groq chat-completions API.

    Flow for each chat() call:
      1. Try the fast zero-LLM regex path (parse_direct_search_request).
      2. If that fires, query the DB and return immediately.
      3. Otherwise, send the user message to Groq with our tool schema.
      4. If Groq returns a tool-call, execute search_listings_db_uz and return results.
      5. If Groq returns a plain text response, return it directly.
    """

    def __init__(self) -> None:
        api_key = settings.groq_api_key if hasattr(settings, "groq_api_key") else None
        api_key = api_key or os.getenv("GROQ_API_KEY")
        self._client: Optional[AsyncGroq] = AsyncGroq(api_key=api_key) if api_key else None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def chat(
        self,
        user_message: str,
        db: AsyncSession,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        # --- Fast path: regex-based direct search (no LLM round-trip) ---
        direct_args = parse_direct_search_request(user_message)
        if direct_args:
            try:
                results = await search_listings_db_uz(db, **direct_args)
            except (TimeoutError, OSError, SQLAlchemyError) as exc:
                print(f"DEBUG: AI DB qidiruv xatosi: {exc}")
                return {
                    "text": (
                        "Kechirasiz, hozir qidiruv bazasi bilan aloqa vaqtincha ishlamayapti. "
                        "Bir ozdan keyin qayta urinib ko'ring."
                    ),
                    "listings": [],
                }
            return {
                "text": format_search_summary(results, direct_args),
                "listings": results,
            }

        # --- Slow path: Groq LLM ---
        if not self._client:
            return {
                "text": "Kechirasiz, AI xizmati sozlanmagan. GROQ_API_KEY ni tekshiring.",
                "listings": [],
            }

        try:
            return await self._chat_with_groq(user_message, db, history)
        except Exception as exc:
            error_msg = str(exc)
            print(f"DEBUG AI Xatosi: {error_msg}")

            if "429" in error_msg or "rate_limit" in error_msg.lower():
                return {
                    "text": (
                        "Kechirasiz, hozirda so'rovlar soni ko'payib ketdi. "
                        "Iltimos, bir ozdan so'ng qayta urinib ko'ring (AI limitga yetdi)."
                    ),
                    "listings": [],
                }

            return {"text": f"Kechirasiz, xatolik yuz berdi: {error_msg}", "listings": []}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _chat_with_groq(
        self,
        user_message: str,
        db: AsyncSession,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        One agentic turn:
          Turn 1 → send user message, check for tool-call.
          Turn 2 → if tool was called, inject DB result and get final reply.
        """
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        # Append sanitised history (role must be "user" or "assistant").
        for h in history or []:
            role = h.get("role", "user")
            if role == "model":
                role = "assistant"
            content = h.get("content") or " ".join(h.get("parts", []))
            messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        print(f"DEBUG: Groq ga so'rov ketmoqda: {user_message!r}")

        # --- Turn 1: ask the model ---
        response = await self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=_TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

        choice = response.choices[0]
        finish_reason = choice.finish_reason
        assistant_msg = choice.message

        print(f"DEBUG: Groq dan javob keldi. finish_reason={finish_reason!r}")

        # --- Handle tool-call ---
        if finish_reason == "tool_calls" and assistant_msg.tool_calls:
            tool_call = assistant_msg.tool_calls[0]
            fn_name = tool_call.function.name
            fn_args: Dict[str, Any] = json.loads(tool_call.function.arguments or "{}")

            print(f"DEBUG: AI funksiya chaqirdi: {fn_name} | Argumentlar: {fn_args}")

            if fn_name == "search_listings_db":
                try:
                    results = await search_listings_db_uz(db, **fn_args)
                except (TimeoutError, OSError, SQLAlchemyError) as exc:
                    print(f"DEBUG: AI DB qidiruv xatosi: {exc}")
                    return {
                        "text": (
                            "Kechirasiz, hozir qidiruv bazasi bilan aloqa vaqtincha ishlamayapti. "
                            "Bir ozdan keyin qayta urinib ko'ring."
                        ),
                        "listings": [],
                    }

                print(f"DEBUG: Baza natijalari: {len(results)} ta topildi")

                # --- Turn 2: send tool result, get human-readable reply ---
                messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": fn_name,
                                    "arguments": tool_call.function.arguments,
                                },
                            }
                        ],
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            {"count": len(results), "listings": results},
                            ensure_ascii=False,
                        ),
                    }
                )

                final_response = await self._client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    max_tokens=1024,
                )
                final_text = final_response.choices[0].message.content or ""

                return {
                    "text": format_search_summary(results, fn_args) if results else final_text,
                    "listings": results,
                }

        # --- Plain text reply (no tool-call) ---
        return {"text": assistant_msg.content or "", "listings": []}


# Singleton consumed by the router
ai_service = AIService()
