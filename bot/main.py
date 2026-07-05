"""Main bot entry point"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from handlers import start
from handlers import registration


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def notify_admins_bot_started(bot: Bot) -> None:
    """Notify configured admins when the bot starts."""
    if not settings.ADMIN_IDS:
        logger.info("No admin IDs configured; skipping startup notification.")
        return

    bot_info = await bot.get_me()
    message = "Aparty bot ishga tushdi."
    if bot_info.username:
        message = f"{message}\nBot: @{bot_info.username}"

    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message)
        except TelegramBadRequest as exc:
            logger.warning(
                "Could not send startup notification to admin %s: %s. "
                "Check that this is a Telegram user chat ID and that the user has started this bot.",
                admin_id,
                exc.message,
            )
        except Exception:
            logger.exception("Failed to send startup notification to admin %s", admin_id)


async def main():
    """Start the bot"""
    # Initialize bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(registration.router)
    
    logger.info("Bot started polling...")
    try:
        await notify_admins_bot_started(bot)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
