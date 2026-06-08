import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN, API_BASE_URL
from bot.handlers import start, books, loans, profile, admin
from bot.middlewares.auth import AuthMiddleware


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Bot'ni sozlash va ishga tushirish."""

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi! .env faylini tekshiring.")
        sys.exit(1)

    # Bot yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Dispatcher xabarlarni route qiladi
    # MemoryStorage FSM data xotirada saqlanadi
    # Productionda RedisStorage ishlatiladi (bot restart bo'lganda data saqlanib qoladi)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # AuthMiddleware har bir xabar/callback da token tekshiriladi
    # va api_client handler'ga inject qilinadi
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    dp.include_router(start.router)
    dp.include_router(books.router)
    dp.include_router(loans.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)

    logger.info("🤖 Bot ishga tushdi...")
    logger.info(f"📡 API manzili: {API_BASE_URL}")

    try:
        # start_polling — Telegram serveridan yangilanishlarni oladi (long polling)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (Ctrl+C)")
