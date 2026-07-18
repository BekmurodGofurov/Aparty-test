"""Registration flow handler — guides new users through sign-up.

FSM flow: Language → Full Name → Role → Phone (via contact button)
On completion: single POST /api/v1/auth/register sent to the backend.

The bot never stores passwords.  Login uses the /login command → code flow.
"""
from contextlib import suppress
from html import escape
import re

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext

from states import RegistrationStates
from utils.messages import get_message
from utils.backend_api import backend_client


router = Router()


def normalize_full_name(value: str) -> str:
    """Normalize whitespace in full name."""
    return " ".join(value.strip().split())


def is_valid_full_name(value: str) -> bool:
    """Require at least first name and last name, without digits or symbols."""
    parts = normalize_full_name(value).split()
    if len(parts) < 2:
        return False

    name_part_pattern = re.compile(r"^[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳʼ'`''-]{2,}$")
    return all(name_part_pattern.fullmatch(part) for part in parts)


def normalize_phone(value: str) -> str:
    """Normalize Uzbek phone numbers to +998XXXXXXXXX."""
    phone = re.sub(r"[\s\-()]", "", value.strip())
    if phone.startswith("998"):
        phone = f"+{phone}"
    return phone


def is_valid_phone(value: str) -> bool:
    """Validate an Uzbek E.164 phone number."""
    return re.fullmatch(r"\+998\d{9}", value) is not None


# ─── Language selection ────────────────────────────────────────────────────────

@router.callback_query(RegistrationStates.waiting_for_language)
async def language_selected(callback: CallbackQuery, state: FSMContext):
    """Handle language selection."""
    lang_map = {
        "lang_uz": "uz",
        "lang_ru": "ru",
        "lang_en": "en",
    }

    language = lang_map.get(callback.data)
    if not language:
        await callback.answer()
        return

    await state.update_data(language=language)
    await state.set_state(RegistrationStates.waiting_for_full_name)

    await callback.message.edit_text(
        get_message(language, "full_name_prompt"),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Full name ────────────────────────────────────────────────────────────────

@router.message(RegistrationStates.waiting_for_full_name)
async def full_name_received(message: Message, state: FSMContext):
    """Handle full name input."""
    name = normalize_full_name(message.text or "")
    data = await state.get_data()
    language = data.get("language", "uz")

    if not is_valid_full_name(name):
        err = {
            "uz": "❌ Iltimos, ism va familyangizni kiriting. Masalan: Ali Valiyev",
            "ru": "❌ Пожалуйста, введите имя и фамилию. Например: Али Валиев",
            "en": "❌ Please enter both first and last name. Example: Ali Valiyev",
        }
        await message.answer(err.get(language, err["en"]))
        return

    await state.update_data(full_name=name)
    await state.set_state(RegistrationStates.waiting_for_role)

    # Role selection keyboard
    roles = {
        "uz": {"owner": "🏠 Kvartira egasi", "realtor": "💼 Makler", "tenant": "👨‍💼 Ijarchi"},
        "ru": {"owner": "🏠 Владелец квартиры", "realtor": "💼 Маклер", "tenant": "👨‍💼 Жилец"},
        "en": {"owner": "🏠 Apartment Owner", "realtor": "💼 Realtor", "tenant": "👨‍💼 Tenant"},
    }
    role_labels = roles.get(language, roles["en"])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=role_labels["owner"], callback_data="role_owner"),
            InlineKeyboardButton(text=role_labels["realtor"], callback_data="role_realtor"),
        ],
        [
            InlineKeyboardButton(text=role_labels["tenant"], callback_data="role_tenant"),
        ],
    ])

    await message.answer(get_message(language, "role_prompt"), reply_markup=keyboard, parse_mode="HTML")


# ─── Role selection ────────────────────────────────────────────────────────────

@router.callback_query(RegistrationStates.waiting_for_role)
async def role_selected(callback: CallbackQuery, state: FSMContext):
    """Handle role selection."""
    role_map = {
        "role_owner": "owner",
        "role_realtor": "makler",
        "role_tenant": "student",
    }

    role = role_map.get(callback.data)
    if not role:
        await callback.answer()
        return

    data = await state.get_data()
    language = data.get("language", "uz")

    await state.update_data(role=role)
    await state.set_state(RegistrationStates.waiting_for_phone)

    # Contact sharing button
    btn_text = {
        "uz": "📱 Kontaktni ulashish",
        "ru": "📱 Поделиться контактом",
        "en": "📱 Share Contact",
    }.get(language, "📱 Share Contact")

    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn_text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    with suppress(TelegramBadRequest):
        await callback.message.delete()

    await callback.message.answer(
        get_message(language, "phone_prompt"),
        reply_markup=phone_keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Phone number (final step) ─────────────────────────────────────────────────

@router.message(RegistrationStates.waiting_for_phone)
async def phone_received(message: Message, state: FSMContext):
    """Handle phone number received via contact sharing — final registration step.

    Security: verifies the user is sharing their OWN Telegram contact.
    On success: sends a single POST /api/v1/auth/register to the backend
    with { id, full_name, role, phone } — no password.
    """
    data = await state.get_data()
    language = data.get("language", "uz")
    full_name = data.get("full_name", "")
    role = data.get("role", "student")

    # Must use contact button
    if not message.contact:
        err = {
            "uz": "❌ Iltimos, quyidagi tugmani bosib kontaktingizni ulashing.",
            "ru": "❌ Пожалуйста, нажмите кнопку и поделитесь контактом.",
            "en": "❌ Please use the button below to share your contact.",
        }
        await message.answer(err.get(language, err["en"]))
        return

    # Security check: user must share their OWN contact
    if not message.contact.user_id or message.contact.user_id != message.from_user.id:
        err = {
            "uz": "❌ Iltimos, faqat o'zingizning Telegram kontaktingizni yuboring.",
            "ru": "❌ Пожалуйста, отправьте только свой Telegram контакт.",
            "en": "❌ Please share only your own Telegram contact.",
        }
        await message.answer(err.get(language, err["en"]))
        return

    phone = normalize_phone(message.contact.phone_number)
    if not is_valid_phone(phone):
        err = {
            "uz": "❌ Telefon raqam noto'g'ri. Raqam +998XXXXXXXXX formatida bo'lishi kerak.",
            "ru": "❌ Неверный номер телефона. Формат должен быть +998XXXXXXXXX.",
            "en": "❌ Invalid phone number. It must be in +998XXXXXXXXX format.",
        }
        await message.answer(err.get(language, err["en"]))
        return

    telegram_id = message.from_user.id

    # Single API call with { id, full_name, role, phone } — no password
    result = await backend_client.register_user(
        telegram_id=telegram_id,
        full_name=full_name,
        phone=phone,
        role=role,
    )

    if result["success"]:
        messages_map = {
            "uz": (
                "✅ <b>Ro'yxatdan o'tdingiz!</b>\n\n"
                "📱 <b>Telefon:</b> <code>{phone}</code>\n\n"
                "💻 Saytga kirish uchun <b>Aparty.uz</b> ni oching va /login "
                "buyrug'i orqali kirish kodini oling.\n"
                "🔐 Kod 2 daqiqa amal qiladi."
            ),
            "ru": (
                "✅ <b>Вы успешно зарегистрированы!</b>\n\n"
                "📱 <b>Телефон:</b> <code>{phone}</code>\n\n"
                "💻 Для входа на <b>Aparty.uz</b> используйте команду /login "
                "чтобы получить одноразовый код.\n"
                "🔐 Код действует 2 минуты."
            ),
            "en": (
                "✅ <b>Registration successful!</b>\n\n"
                "📱 <b>Phone:</b> <code>{phone}</code>\n\n"
                "💻 To log in to <b>Aparty.uz</b>, use the /login command "
                "to get a one-time code.\n"
                "🔐 The code is valid for 2 minutes."
            ),
        }
        text = messages_map.get(language, messages_map["en"]).format(
            phone=escape(phone),
        )
        await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    else:
        error_detail = escape(result.get("error", "Noma'lum xato"))
        err_map = {
            "uz": f"❌ Xatolik yuz berdi:\n<code>{error_detail}</code>",
            "ru": f"❌ Произошла ошибка:\n<code>{error_detail}</code>",
            "en": f"❌ An error occurred:\n<code>{error_detail}</code>",
        }
        await message.answer(
            err_map.get(language, err_map["en"]),
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )

    await state.clear()
