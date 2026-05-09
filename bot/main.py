import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from bot.config import BOT_TOKEN
from bot.handlers import start, books

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Handlerlarni ro'yxatdan o'tkazish
    dp.include_router(start.router)
    dp.include_router(books.router)

    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
