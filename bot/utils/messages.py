MESSAGES = {
    "uz": {
        "greeting": "👋 Xush kelibsiz!\n\nBotga xush kelibsiz. Iltimos, tilni tanlang:",
        "language_selected": "✅ Til: O'zbekcha",
        "full_name_prompt": "👤 Iltimos, ism-familiyangizni kiriting:",
        "role_prompt": "🎯 Iltimos, rolni tanlang:",
        "phone_prompt": "📱 Iltimos, telefon raqamingizni yuboring:",
        "confirmation": "✅ Ro'yxatdan o'tdingiz!\n\n📱 Telefon: {phone}\n🔑 Parol: {password}",
        "role_owner": "🏠 Kvartira egasi",
        "role_realtor": "💼 Makler",
        "role_tenant": "👨‍💼 Ijarchi",
    },
    "ru": {
        "greeting": "👋 Добро пожаловать!\n\nДобро пожаловать в бота. Пожалуйста, выберите язык:",
        "language_selected": "✅ Язык: Русский",
        "full_name_prompt": "👤 Пожалуйста, введите ваше имя и фамилию:",
        "role_prompt": "🎯 Пожалуйста, выберите роль:",
        "phone_prompt": "📱 Пожалуйста, отправьте номер телефона:",
        "confirmation": "✅ Вы зарегистрированы!\n\n📱 Телефон: {phone}\n🔑 Пароль: {password}",
        "role_owner": "🏠 Владелец квартиры",
        "role_realtor": "💼 Риэлтор",
        "role_tenant": "👨‍💼 Арендатор",
    },
    "en": {
        "greeting": "👋 Welcome!\n\nWelcome to the bot. Please select a language:",
        "language_selected": "✅ Language: English",
        "full_name_prompt": "👤 Please enter your full name (First and Last name):",
        "role_prompt": "🎯 Please select your role:",
        "phone_prompt": "📱 Please share your phone number:",
        "confirmation": "✅ You have registered!\n\n📱 Phone: {phone}\n🔑 Password: {password}",
        "role_owner": "🏠 Apartment Owner",
        "role_realtor": "💼 Realtor",
        "role_tenant": "👨‍💼 Tenant",
    }
}


def get_message(language: str, key: str) -> str:
    """Get translated message"""
    return MESSAGES.get(language, MESSAGES["en"]).get(key, f"Missing message for {key}")
