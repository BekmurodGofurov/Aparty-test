"""Telegram Bot API delivery. The Telegram id of a user is also their id in Aparty."""

from __future__ import annotations

import logging
from html import escape
from typing import Optional

import httpx

from app.config import settings
from app.constants import TELEGRAM_FAILED, TELEGRAM_SENT, TELEGRAM_SKIPPED

logger = logging.getLogger(__name__)


def _escape(value: str) -> str:
    """Telegram HTML only needs &, < and > escaped."""
    return escape(value, quote=False)


def _text(title: str, body: Optional[str], target_url: Optional[str]) -> str:
    parts = [f"<b>{_escape(title)}</b>"]
    if body:
        parts.append(_escape(body))
    if settings.site_url and target_url:
        parts.append(_escape(f"{settings.site_url.rstrip('/')}{target_url}"))
    return "\n".join(parts)


async def send_message(chat_id: int, title: str, body: Optional[str], target_url: Optional[str]) -> str:
    """Send one message. Returns a delivery state and never raises: a failed message must not block the queue."""
    if not settings.bot_token:
        return TELEGRAM_SKIPPED

    # The token is part of the URL, so never log the URL or the raw exception text.
    url = f"{settings.telegram_api_url}/bot{settings.bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": _text(title, body, target_url), "parse_mode": "HTML",
               "disable_web_page_preview": True}
    try:
        async with httpx.AsyncClient(timeout=settings.telegram_request_timeout_seconds) as client:
            response = await client.post(url, json=payload)
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Telegram message to %s failed (%s)", chat_id, type(exc).__name__)
        return TELEGRAM_FAILED

    if response.status_code == 200 and data.get("ok"):
        return TELEGRAM_SENT
    logger.warning("Telegram rejected the message to %s: %s", chat_id, data.get("description", response.status_code))
    return TELEGRAM_FAILED
