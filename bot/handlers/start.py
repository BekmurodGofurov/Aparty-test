"""Start command handler. Sign-in and registration happen on the website via Telegram login."""
from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.settings import settings


router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    """Greet the user and point them to the website."""
    name = escape(message.from_user.first_name or "")
    text = (
        f"👋 Xush kelibsiz, <b>{name}</b>!\n\n"
        "🏠 <b>Aparty.uz</b> — ko'chmas mulk platformasi.\n"
        "Saytga kirish yoki ro'yxatdan o'tish uchun saytdagi "
        "<b>«Telegram orqali kirish»</b> tugmasidan foydalaning."
    )
    keyboard = None
    if settings.SITE_URL:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Saytni ochish", url=settings.SITE_URL)]]
        )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
