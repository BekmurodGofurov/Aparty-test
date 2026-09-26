import uuid

import pytest

from app.handlers import handle_event
from app.schemas import PublicProfile
from tests.conftest import stored_notifications

OWNER = 10
REQUESTER = 20
RESIDENT = 30
BOOKING = str(uuid.uuid4())


def booking_event(event="booking.created", status="pending", **overrides):
    payload = {
        "event": event, "booking_id": BOOKING, "listing_id": str(uuid.uuid4()), "listing_title": "Sunny flat",
        "user_id": REQUESTER, "owner_id": OWNER, "actor_id": REQUESTER, "approver_ids": [OWNER],
        "start_date": "2030-01-10", "end_date": "2030-01-20", "status": status, "is_roommate_request": False,
    }
    payload.update(overrides)
    return payload


def ad_event(**overrides):
    payload = {
        "event": "listing.created", "id": str(uuid.uuid4()), "owner_id": REQUESTER, "source": "roommate",
        "apartment_owner_id": OWNER, "apartment_title": "Sunny flat", "available_spaces": 2, "target_gender": "female",
    }
    payload.update(overrides)
    return payload


async def titles(engine, user_id):
    return [item.title for item in await stored_notifications(engine, user_id)]


async def test_booking_request_notifies_the_owner_with_name_listing_and_dates(engine, iam_profiles):
    iam_profiles[REQUESTER] = PublicProfile(id=REQUESTER, full_name="Malika Karimova")
    await handle_event(booking_event())

    [item] = await stored_notifications(engine, OWNER)
    assert item.type == "booking_requested"
    assert item.title == "Yangi bron so'rovi"
    assert "Malika Karimova" in item.body and "«Sunny flat»" in item.body and "2030-01-10 — 2030-01-20" in item.body
    assert item.target_url == "/my-bookings"
    assert await stored_notifications(engine, REQUESTER) == []


async def test_name_falls_back_when_iam_is_unavailable(engine):
    await handle_event(booking_event())
    [item] = await stored_notifications(engine, OWNER)
    assert item.body.startswith("Foydalanuvchi ")


async def test_roommate_request_reaches_the_poster_and_every_resident_but_not_the_requester(engine):
    await handle_event(booking_event(is_roommate_request=True, approver_ids=[OWNER, RESIDENT]))
    assert await titles(engine, OWNER) == ["Yangi sherik so'rovi"]
    assert await titles(engine, RESIDENT) == ["Yangi sherik so'rovi"]
    assert await titles(engine, REQUESTER) == []


async def test_request_without_approvers_notifies_nobody(engine):
    await handle_event(booking_event(approver_ids=[]))
    assert await stored_notifications(engine) == []


@pytest.mark.parametrize("status,title", [("confirmed", "So'rovingiz qabul qilindi"), ("rejected", "So'rovingiz rad etildi")])
async def test_answers_go_to_the_requester(engine, status, title):
    await handle_event(booking_event("booking.updated", status=status, actor_id=OWNER))
    assert await titles(engine, REQUESTER) == [title]
    assert await stored_notifications(engine, OWNER) == []


async def test_cancelling_by_the_requester_tells_the_people_who_answer(engine, iam_profiles):
    iam_profiles[REQUESTER] = PublicProfile(id=REQUESTER, full_name="Malika Karimova")
    await handle_event(booking_event("booking.updated", status="cancelled", actor_id=REQUESTER, approver_ids=[OWNER, RESIDENT]))

    for user in (OWNER, RESIDENT):
        [item] = await stored_notifications(engine, user)
        assert item.title == "Bron bekor qilindi" and "Malika Karimova" in item.body
    assert await stored_notifications(engine, REQUESTER) == []


async def test_cancelling_by_someone_else_tells_the_requester(engine):
    await handle_event(booking_event("booking.updated", status="cancelled", actor_id=OWNER))
    [item] = await stored_notifications(engine, REQUESTER)
    assert "e'lon egasi tomonidan" in item.body
    assert await stored_notifications(engine, OWNER) == []


async def test_other_booking_statuses_are_ignored(engine):
    await handle_event(booking_event("booking.updated", status="pending"))
    assert await stored_notifications(engine) == []


async def test_roommate_ad_notifies_the_apartment_owner(engine):
    payload = ad_event()
    await handle_event(payload)

    [item] = await stored_notifications(engine, OWNER)
    assert item.type == "roommate_ad_posted"
    assert item.title == "Ijarachilaringiz sherik qidirmoqda"
    assert "«Sunny flat»" in item.body and "2 kishi (ayol)" in item.body
    assert item.target_url == f"/listing/{payload['id']}"


async def test_ads_without_a_gender_preference_do_not_mention_one(engine):
    await handle_event(ad_event(target_gender="mixed", available_spaces=1))
    [item] = await stored_notifications(engine, OWNER)
    assert "1 kishi qidirishyapti" in item.body


async def test_ordinary_listings_and_incomplete_ads_are_ignored(engine):
    await handle_event(ad_event(source="owner"))
    await handle_event(ad_event(apartment_owner_id=None))
    await handle_event({"event": "listing.updated", "id": str(uuid.uuid4())})
    await handle_event({"event": "something.else"})
    await handle_event({})
    assert await stored_notifications(engine) == []


async def test_the_same_event_delivered_twice_creates_one_notification_and_one_message(engine, telegram):
    payload = booking_event()
    await handle_event(payload)
    await handle_event(payload)
    assert len(await stored_notifications(engine, OWNER)) == 1
    assert len(telegram.calls) == 1


async def test_a_new_status_of_the_same_booking_is_a_new_notification(engine):
    await handle_event(booking_event("booking.updated", status="confirmed"))
    await handle_event(booking_event("booking.updated", status="cancelled", actor_id=OWNER))
    assert len(await stored_notifications(engine, REQUESTER)) == 2
