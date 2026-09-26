from types import SimpleNamespace
from unittest.mock import AsyncMock

from config.settings import settings
from handlers.start import start_handler


def make_message(first_name="Aziz"):
    return SimpleNamespace(from_user=SimpleNamespace(first_name=first_name), answer=AsyncMock())


async def test_start_greets_by_name_and_links_to_the_site(monkeypatch):
    monkeypatch.setattr(settings, "SITE_URL", "https://aparty.example")
    message = make_message()

    await start_handler(message)

    text = message.answer.await_args.args[0]
    keyboard = message.answer.await_args.kwargs["reply_markup"]
    assert "Aziz" in text
    assert keyboard.inline_keyboard[0][0].url == "https://aparty.example"


async def test_start_without_site_url_sends_no_button(monkeypatch):
    monkeypatch.setattr(settings, "SITE_URL", "")
    message = make_message()

    await start_handler(message)

    assert message.answer.await_args.kwargs["reply_markup"] is None


async def test_start_escapes_html_in_the_name(monkeypatch):
    monkeypatch.setattr(settings, "SITE_URL", "")
    message = make_message("<b>x</b>")

    await start_handler(message)

    assert "<b>x</b>" not in message.answer.await_args.args[0]
    assert "&lt;b&gt;" in message.answer.await_args.args[0]
