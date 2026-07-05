"""Start command handler — checks if user is registered via backend API"""
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states import RegistrationStates
from utils.backend_api import backend_client


router = Router()


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    """Handle /start command"""
    telegram_id = message.from_user.id
    await state.clear()

    # Check via backend API if user already registered with this Telegram ID
    check_result = await backend_client.check_user_by_telegram_id(telegram_id)
    api_data = check_result.get("data", {})
    user_data = api_data.get("data", {}) if isinstance(api_data, dict) else {}

    if not check_result.get("success"):
        await message.answer(
            "❌ Bazaga ulanishda xatolik yuz berdi. Iltimos, birozdan keyin qayta urinib ko'ring."
        )
        return

    if user_data.get("exists"):
        full_name = user_data.get("full_name", "")
        await message.answer(
            f"👋 Xush kelibsiz, {full_name}!\n\n"
            f"✅ Siz allaqachon ro'yxatdan o'tgansiz.\n"
            f"💻 Aparty.uz saytiga telefon va parolingiz bilan kiring.",
        )
        return

    # New user — start registration flow
    await state.set_state(RegistrationStates.waiting_for_language)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        ],
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
        ],
    ])

    await message.answer(
        "👋 Xush kelibsiz! / Добро пожаловать! / Welcome!\n\n"
        "🏠 <b>Aparty.uz</b> — ko'chmas mulk platformasi\n\n"
        "Ro'yxatdan o'tish uchun tilni tanlang:\n"
        "Для регистрации выберите язык:\n"
        "Select language to register:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
