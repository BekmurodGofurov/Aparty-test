"""
Unit tests for backend/app/services/ai_service.py — Groq backend.

Coverage:
  - normalize_amenities
  - format_listing_results
  - format_search_summary
  - parse_direct_search_request
  - AIService.chat  (direct/fast path)
  - AIService.chat  (Groq path — plain text reply)
  - AIService.chat  (Groq path — tool-call → DB search → results)
  - AIService.chat  (Groq path — rate-limit 429 error handling)
  - AIService.chat  (no API key configured)
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_service import (
    AIService,
    format_listing_results,
    format_search_summary,
    normalize_amenities,
    parse_direct_search_request,
)


# ---------------------------------------------------------------------------
# Helpers — build fake Groq response objects
# ---------------------------------------------------------------------------


def _make_plain_response(text: str):
    """Simulate a Groq ChatCompletion with a plain-text reply."""
    message = SimpleNamespace(
        content=text,
        tool_calls=None,
    )
    choice = SimpleNamespace(
        finish_reason="stop",
        message=message,
    )
    return SimpleNamespace(choices=[choice])


def _make_tool_call_response(fn_name: str, fn_args: dict, call_id: str = "call_123"):
    """Simulate a Groq ChatCompletion that requests a tool call."""
    tool_call = SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(
            name=fn_name,
            arguments=json.dumps(fn_args, ensure_ascii=False),
        ),
    )
    message = SimpleNamespace(
        content=None,
        tool_calls=[tool_call],
    )
    choice = SimpleNamespace(
        finish_reason="tool_calls",
        message=message,
    )
    return SimpleNamespace(choices=[choice])


# ---------------------------------------------------------------------------
# Pure utility tests — no mocking needed
# ---------------------------------------------------------------------------


class TestNormalizeAmenities:
    def test_known_alias_ac(self):
        assert normalize_amenities(["ac"]) == ["ac"]

    def test_known_alias_wifi(self):
        assert normalize_amenities(["wi-fi"]) == ["wifi"]

    def test_deduplication(self):
        assert normalize_amenities(["wifi", "wi-fi"]) == ["wifi"]

    def test_empty_input(self):
        assert normalize_amenities([]) == []
        assert normalize_amenities(None) == []

    def test_unknown_alias_ignored(self):
        assert normalize_amenities(["unknown_thing"]) == []


class TestFormatListingResults:
    def test_empty_returns_not_found_message(self):
        result = format_listing_results([])
        assert "mavjud emas" in result

    def test_single_listing_formatted(self):
        listings = [
            {
                "price": "200$",
                "address": "Toshkent, Yunusobod",
                "rooms": 2,
                "gender": "mixed",
                "distance_text": None,
                "is_roommate_listing": False,
                "amenities": ["wifi"],
            }
        ]
        result = format_listing_results(listings)
        assert "200$" in result
        assert "Yunusobod" in result
        assert "wifi" in result

    def test_roommate_source_text_added(self):
        listings = [
            {
                "price": "150$",
                "address": "Andijon",
                "rooms": 1,
                "gender": "male",
                "distance_text": "1.5 km uzoqlikda",
                "is_roommate_listing": True,
                "amenities": [],
            }
        ]
        result = format_listing_results(listings)
        assert "Roommate" in result


class TestFormatSearchSummary:
    def test_empty_results(self):
        result = format_search_summary([], {})
        assert "topilmadi" in result

    def test_with_joy_nomi(self):
        args = {"joy_nomi": "Sharda University", "resolved_place_name": "Sharda University"}
        result = format_search_summary([{"id": "1"}], args)
        assert "Sharda University" in result
        assert "1 ta" in result

    def test_with_price_range(self):
        args = {"min_narx": 100, "max_narx": 300}
        result = format_search_summary([{}, {}], args)
        assert "2 ta" in result
        assert "100$ dan" in result
        assert "300$ gacha" in result

    def test_plain_count_when_no_filters(self):
        result = format_search_summary([{}, {}, {}], {})
        assert "3 ta" in result


class TestParseDirectSearchRequest:
    def test_empty_message_returns_none(self):
        assert parse_direct_search_request("") is None
        assert parse_direct_search_request("   ") is None

    def test_non_search_message_returns_none(self):
        # Generic greeting with no search keywords
        assert parse_direct_search_request("salom") is None

    def test_price_max_parsed(self):
        args = parse_direct_search_request("300$ gacha kvartira kerak")
        assert args is not None
        assert args.get("max_narx") == 300

    def test_price_min_parsed(self):
        args = parse_direct_search_request("200$ dan kvartira")
        assert args is not None
        assert args.get("min_narx") == 200

    def test_rooms_parsed(self):
        args = parse_direct_search_request("2 xonali uy kerak")
        assert args is not None
        assert args.get("xonalar") == 2

    def test_gender_erkak(self):
        args = parse_direct_search_request("erkaklar uchun uy")
        assert args is not None
        assert args.get("jins") == "male"

    def test_gender_ayol(self):
        args = parse_direct_search_request("qizlar uchun kvartira")
        assert args is not None
        assert args.get("jins") == "female"

    def test_roommate_flag(self):
        args = parse_direct_search_request("roommate kerak bo'sh joy")
        assert args is not None
        assert args.get("roommate") is True

    def test_wifi_amenity(self):
        args = parse_direct_search_request("wifi bor kvartira")
        assert args is not None
        assert "wifi" in (args.get("qulayliklar") or [])

    def test_ac_amenity_normalized(self):
        args = parse_direct_search_request("ac bor uy kerak")
        assert args is not None
        assert "ac" in (args.get("qulayliklar") or [])


# ---------------------------------------------------------------------------
# AIService — unit tests with mocked Groq client
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_db():
    """A simple async mock for the database session."""
    return AsyncMock()


@pytest.fixture()
def service():
    """
    Return an AIService instance with its internal AsyncGroq client replaced
    by a MagicMock so we never touch the network.
    """
    svc = AIService.__new__(AIService)
    svc._client = MagicMock()
    # Groq's client.chat.completions.create is a coroutine in AsyncGroq
    svc._client.chat = MagicMock()
    svc._client.chat.completions = MagicMock()
    svc._client.chat.completions.create = AsyncMock()
    return svc


class TestAIServiceNoApiKey:
    """When no API key is configured, the service must degrade gracefully."""

    @pytest.mark.asyncio
    async def test_chat_returns_error_message(self, mock_db):
        svc = AIService.__new__(AIService)
        svc._client = None  # simulate no key

        result = await svc.chat("salom", mock_db)

        assert "GROQ_API_KEY" in result["text"]
        assert result["listings"] == []


class TestAIServiceDirectPath:
    """Messages matching the regex fast-path must never hit Groq."""

    @pytest.mark.asyncio
    async def test_direct_search_bypasses_groq(self, service, mock_db):
        fake_listings = [
            {
                "id": "abc",
                "price": "250$",
                "address": "Toshkent, Mirzo Ulugbek",
                "rooms": 2,
                "gender": "mixed",
                "distance_text": None,
                "is_roommate_listing": False,
                "amenities": [],
                "url": "/listing/abc",
                "price_usd": 250,
                "region": "Toshkent",
                "district": "Mirzo Ulugbek",
                "source": "makler",
                "available_spaces": 1,
                "max_occupants": 3,
                "distance_km": None,
                "near_place": None,
                "image": None,
                "description": "",
            }
        ]

        with patch(
            "app.services.ai_service.search_listings_db_uz",
            new=AsyncMock(return_value=fake_listings),
        ):
            result = await service.chat("300$ gacha kvartira kerak", mock_db)

        # Groq client must NOT have been called
        service._client.chat.completions.create.assert_not_called()

        assert result["listings"] == fake_listings
        assert isinstance(result["text"], str)

    @pytest.mark.asyncio
    async def test_direct_path_db_error_returns_graceful_message(self, mock_db):
        """
        When the fast-path regex matches AND the DB raises an error,
        the service must return a graceful error message without crashing.
        """
        from sqlalchemy.exc import SQLAlchemyError

        # Build a service with NO client so the Groq slow-path cannot interfere
        svc = AIService.__new__(AIService)
        svc._client = None

        with patch(
            "app.services.ai_service.search_listings_db_uz",
            new=AsyncMock(side_effect=SQLAlchemyError("connection refused")),
        ):
            # "300$ gacha kvartira" reliably hits the direct (regex) path
            result = await svc.chat("300$ gacha kvartira kerak", mock_db)

        assert "ishlamayapti" in result["text"]
        assert result["listings"] == []


class TestAIServiceGroqPlainText:
    """Groq returns a plain text reply (no tool call)."""

    @pytest.mark.asyncio
    async def test_plain_reply_returned(self, service, mock_db):
        service._client.chat.completions.create.return_value = _make_plain_response(
            "Salom! Sizga qanday yordam bera olaman?"
        )

        result = await service.chat("salom necha pul?", mock_db)

        assert result["text"] == "Salom! Sizga qanday yordam bera olaman?"
        assert result["listings"] == []
        # Exactly one Groq call (no second turn needed)
        assert service._client.chat.completions.create.call_count == 1


class TestAIServiceGroqToolCall:
    """Groq requests the search_listings_db tool — full two-turn flow."""

    @pytest.mark.asyncio
    async def test_tool_call_triggers_db_search_and_returns_listings(
        self, service, mock_db
    ):
        turn1 = _make_tool_call_response(
            "search_listings_db",
            {"viloyat": "Andijon", "max_narx": 250},
        )
        turn2 = _make_plain_response("Andijon bo'yicha 1 ta variant topdim.")

        service._client.chat.completions.create.side_effect = [turn1, turn2]

        fake_listings = [
            {
                "id": "xyz",
                "price": "200$",
                "address": "Andijon, Asaka",
                "rooms": 1,
                "gender": "mixed",
                "distance_text": None,
                "is_roommate_listing": False,
                "amenities": [],
                "url": "/listing/xyz",
                "price_usd": 200,
                "region": "Andijon",
                "district": "Asaka",
                "source": "makler",
                "available_spaces": 1,
                "max_occupants": 2,
                "distance_km": None,
                "near_place": None,
                "image": None,
                "description": "",
            }
        ]

        with patch(
            "app.services.ai_service.search_listings_db_uz",
            new=AsyncMock(return_value=fake_listings),
        ):
            # Use a message that does NOT match the regex fast-path so Groq is called
            result = await service.chat(
                "Menga Andijon shahridan arzon uy topib bering", mock_db
            )

        assert result["listings"] == fake_listings
        assert isinstance(result["text"], str)
        assert len(result["text"]) > 0
        # Two turns: first the tool-call request, then the final answer
        assert service._client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_tool_call_db_error_returns_graceful_message(self, service, mock_db):
        from sqlalchemy.exc import SQLAlchemyError

        turn1 = _make_tool_call_response(
            "search_listings_db",
            {"viloyat": "Samarqand"},
        )
        service._client.chat.completions.create.return_value = turn1

        with patch(
            "app.services.ai_service.search_listings_db_uz",
            new=AsyncMock(side_effect=SQLAlchemyError("timeout")),
        ):
            result = await service.chat("Samarqandda uy", mock_db)

        assert "ishlamayapti" in result["text"]
        assert result["listings"] == []


class TestAIServiceGroqRateLimitError:
    """A 429 / rate-limit exception from Groq must produce a user-friendly message."""

    @pytest.mark.asyncio
    async def test_rate_limit_returns_friendly_message(self, service, mock_db):
        service._client.chat.completions.create.side_effect = Exception(
            "429 rate_limit exceeded"
        )

        result = await service.chat("uy kerak bor mi?", mock_db)

        assert "limitga yetdi" in result["text"]
        assert result["listings"] == []

    @pytest.mark.asyncio
    async def test_generic_error_returns_error_text(self, service, mock_db):
        service._client.chat.completions.create.side_effect = Exception(
            "Internal server error"
        )

        result = await service.chat("uy kerak bor mi?", mock_db)

        assert "xatolik" in result["text"]
        assert result["listings"] == []


class TestAIServiceHistory:
    """Chat history is forwarded to Groq with correct role mapping."""

    @pytest.mark.asyncio
    async def test_model_role_converted_to_assistant(self, service, mock_db):
        service._client.chat.completions.create.return_value = _make_plain_response(
            "Albatta yordam beraman!"
        )

        history = [
            {"role": "user", "parts": ["salom"]},
            {"role": "model", "parts": ["Salom! Yordam beray?"]},
        ]

        await service.chat("rahmat", mock_db, history=history)

        call_kwargs = service._client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs.args[0]
        roles = [m["role"] for m in messages]

        # "model" must be converted to "assistant"
        assert "model" not in roles
        assert "assistant" in roles
