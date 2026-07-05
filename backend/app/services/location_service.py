from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class KnownPlace:
    name: str
    aliases: tuple[str, ...]
    latitude: float
    longitude: float
    region: str
    district: str
    address: str


KNOWN_PLACES: tuple[KnownPlace, ...] = (
    KnownPlace(
        name="Sharda University Uzbekistan",
        aliases=(
            "sharda",
            "sharda university",
            "sharda universitet",
            "sharda universit",
            "sharda unversitet",
            "sharda universiteti",
            "sharda university uzbekistan",
            "o'zbekistondagi sharda universiteti",
            "sharda uzbekistan",
        ),
        latitude=40.77271,
        longitude=72.33905,
        region="Andijon",
        district="Andijon shahar",
        address="73, Boburshoh prospekti",
    ),
)


_WORD_RE = re.compile(r"[^a-z0-9а-яёғқўҳ' ]+", re.IGNORECASE)


def normalize_place_text(value: str) -> str:
    text = (value or "").lower()
    replacements = {
        "университет": "universitet",
        "шарда": "sharda",
        "узбекистан": "uzbekistan",
        "ў": "o",
        "ғ": "g",
        "қ": "q",
        "ҳ": "h",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = _WORD_RE.sub(" ", text)
    return " ".join(text.split())


def find_known_place(text: Optional[str]) -> Optional[KnownPlace]:
    if not text:
        return None

    normalized = normalize_place_text(text)
    if not normalized:
        return None

    for place in KNOWN_PLACES:
        for alias in place.aliases:
            alias_normalized = normalize_place_text(alias)
            if alias_normalized and alias_normalized in normalized:
                return place
    return None


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
