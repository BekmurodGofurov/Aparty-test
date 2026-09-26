import logging
import uuid

from app.handlers import handle_event
from tests.conftest import TEST_BOT_TOKEN, stored_notifications

OWNER = 10
EVENT = {
    "event": "booking.created", "booking_id": str(uuid.uuid4()), "listing_title": "Sunny <flat>", "user_id": 20,
    "actor_id": 20, "approver_ids": [OWNER], "start_date": "2030-01-10", "end_date": "2030-01-20", "status": "pending",
}


async def test_owner_gets_a_telegram_message_with_a_link(engine, telegram):
    await handle_event(EVENT)

    assert len(telegram.calls) == 1
    call = telegram.calls[0]
    assert call["chat_id"] == OWNER
    assert call["parse_mode"] == "HTML"
    assert call["text"].startswith("<b>Yangi bron so'rovi</b>")
    assert call["text"].endswith("https://aparty.test/my-bookings")
    assert telegram.urls[0] == f"https://api.telegram.org/bot{TEST_BOT_TOKEN}/sendMessage"
    [item] = await stored_notifications(engine, OWNER)
    assert item.telegram_status == "sent"


async def test_user_text_is_html_escaped(telegram):
    await handle_event(EVENT)
    assert "Sunny &lt;flat&gt;" in telegram.calls[0]["text"]
    assert "<flat>" not in telegram.calls[0]["text"]


async def test_without_a_bot_token_only_the_site_notification_is_created(engine, telegram, monkeypatch):
    monkeypatch.setattr("app.services.telegram.settings.bot_token", None)
    await handle_event(EVENT)

    assert telegram.calls == []
    [item] = await stored_notifications(engine, OWNER)
    assert item.telegram_status == "skipped"


async def test_link_is_left_out_when_the_site_url_is_not_configured(telegram, monkeypatch):
    monkeypatch.setattr("app.services.telegram.settings.site_url", None)
    await handle_event(EVENT)
    assert "http" not in telegram.calls[0]["text"]


async def test_a_user_who_cannot_receive_messages_keeps_the_site_notification(engine, telegram):
    telegram.status_code = 403
    telegram.response = {"ok": False, "description": "Forbidden: bot can't initiate conversation with a user"}
    await handle_event(EVENT)

    [item] = await stored_notifications(engine, OWNER)
    assert item.telegram_status == "failed"
    assert item.title == "Yangi bron so'rovi"


async def test_a_network_failure_does_not_lose_the_notification_or_raise(engine, telegram):
    telegram.raise_network_error = True
    await handle_event(EVENT)
    [item] = await stored_notifications(engine, OWNER)
    assert item.telegram_status == "failed"


async def test_the_bot_token_never_reaches_the_logs(telegram, caplog):
    telegram.raise_network_error = True
    with caplog.at_level(logging.DEBUG):
        await handle_event(EVENT)
        telegram.raise_network_error = False
        telegram.status_code = 403
        telegram.response = {"ok": False, "description": "Forbidden"}
        await handle_event({**EVENT, "booking_id": str(uuid.uuid4())})
    assert TEST_BOT_TOKEN not in caplog.text
    assert "failed" in caplog.text or "rejected" in caplog.text


async def test_one_failed_recipient_does_not_stop_the_others(engine, telegram):
    telegram.status_code = 400
    telegram.response = {"ok": False, "description": "chat not found"}
    await handle_event({**EVENT, "approver_ids": [OWNER, 11]})
    assert len(await stored_notifications(engine)) == 2
