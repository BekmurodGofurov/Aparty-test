"""Login command handler — generates a one-time login code for the website.

Flow:
  1. User sends /login to the bot.
  2. Bot calls POST /api/v1/auth/bot/login-code with { "id": telegram_id }.
  3. Backend generates a CSPRNG 6-digit code, stores it in memory (2-min TTL,
     single-use), and returns it in the response body.
  4. Bot displays the code to the user.
  5. User opens Aparty.uz, enters the 6-digit code.
  6. React calls POST /api/v1/auth/login with { "code": "..." }.
  7. Backend validates, issues JWT, deletes code.

The backend NEVER sends anything to Telegram — the bot is the display layer.
"""
from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from utils.backend_api import backend_client


router = Router()


@router.message(Command("login"))
async def login_handler(message: Message):
    """Generate and display a one-time 6-digit login code.

    The user types this code on the Aparty.uz website login page.
    The code expires in 2 minutes and can only be used once.
    """
    telegram_id = message.from_user.id

    result = await backend_client.request_login_code(telegram_id)

    if not result.get("success"):
        error = escape(result.get("error", "Noma'lum xato"))
        await message.answer(
            f"❌ <b>Xatolik:</b> {error}\n\n"
            f"Agar siz ro'yxatdan o'tmagan bo'lsangiz, /start buyrug'ini yuboring.",
            parse_mode="HTML",
        )
        return

    # The code is inside the nested data structure returned by _make_request
    response_data = result.get("data", {})
    code = response_data.get("code")

    if not code:
        await message.answer(
            "❌ Kod olishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
        )
        return

    await message.answer(
        f"🔐 <b>Aparty.uz kirish kodi</b>\n\n"
        f"Saytga kirish uchun quyidagi kodni kiriting:\n\n"
        f"<code>{escape(code)}</code>\n\n"
        f"⏱ Kod <b>2 daqiqa</b> davomida amal qiladi.\n"
        f"🔒 Kod faqat <b>bir marta</b> ishlatilishi mumkin.\n\n"
        f"<i>Agar siz bu so'rovni yubormagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring.</i>",
        parse_mode="HTML",
    )
