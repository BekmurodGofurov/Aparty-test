"""Notification texts (Uzbek, the language of the site). Each builder returns a Message."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.constants import (
    BOOKINGS_PAGE,
    TYPE_BOOKING_CANCELLED,
    TYPE_BOOKING_CONFIRMED,
    TYPE_BOOKING_REJECTED,
    TYPE_BOOKING_REQUESTED,
    TYPE_ROOMMATE_AD_POSTED,
    TYPE_ROOMMATE_REQUESTED,
)

FALLBACK_NAME = "Foydalanuvchi"
FALLBACK_LISTING = "e'lon"
WANTED_GENDER = {"male": " (erkak)", "female": " (ayol)"}


@dataclass(frozen=True)
class Message:
    type: str
    title: str
    body: str
    target_url: Optional[str] = None


def _dates(payload: dict) -> str:
    return f"{payload.get('start_date')} — {payload.get('end_date')}"


def _listing(payload: dict) -> str:
    return f"«{payload.get('listing_title') or FALLBACK_LISTING}»"


def booking_requested(payload: dict, requester_name: Optional[str]) -> Message:
    name = requester_name or FALLBACK_NAME
    if payload.get("is_roommate_request"):
        return Message(
            TYPE_ROOMMATE_REQUESTED,
            "Yangi sherik so'rovi",
            f"{name} sherik bo'lishni xohlaydi: {_dates(payload)}.",
            BOOKINGS_PAGE,
        )
    return Message(
        TYPE_BOOKING_REQUESTED,
        "Yangi bron so'rovi",
        f"{name} {_listing(payload)} uchun {_dates(payload)} sanalariga so'rov yubordi.",
        BOOKINGS_PAGE,
    )


def booking_confirmed(payload: dict) -> Message:
    return Message(
        TYPE_BOOKING_CONFIRMED,
        "So'rovingiz qabul qilindi",
        f"{_listing(payload)} uchun {_dates(payload)} bron tasdiqlandi.",
        BOOKINGS_PAGE,
    )


def booking_rejected(payload: dict) -> Message:
    return Message(
        TYPE_BOOKING_REJECTED,
        "So'rovingiz rad etildi",
        f"{_listing(payload)} uchun {_dates(payload)} so'rovingiz rad etildi.",
        BOOKINGS_PAGE,
    )


def cancelled_by_requester(payload: dict, requester_name: Optional[str]) -> Message:
    name = requester_name or FALLBACK_NAME
    return Message(
        TYPE_BOOKING_CANCELLED,
        "Bron bekor qilindi",
        f"{name} {_listing(payload)} uchun {_dates(payload)} bronni bekor qildi.",
        BOOKINGS_PAGE,
    )


def cancelled_by_other(payload: dict) -> Message:
    return Message(
        TYPE_BOOKING_CANCELLED,
        "Bron bekor qilindi",
        f"{_listing(payload)} uchun {_dates(payload)} bron e'lon egasi tomonidan bekor qilindi.",
        BOOKINGS_PAGE,
    )


def roommate_ad_posted(payload: dict) -> Message:
    spaces = payload.get("available_spaces") or 1
    wanted = WANTED_GENDER.get(payload.get("target_gender"), "")
    apartment = payload.get("apartment_title") or FALLBACK_LISTING
    return Message(
        TYPE_ROOMMATE_AD_POSTED,
        "Ijarachilaringiz sherik qidirmoqda",
        f"«{apartment}» kvartirangizda yashovchilar yana {spaces} kishi{wanted} qidirishyapti.",
        f"/listing/{payload['id']}",
    )
