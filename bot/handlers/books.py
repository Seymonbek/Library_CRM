import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.config import API_BASE_URL

router = Router()


@router.message(Command("books"))
async def cmd_books(message: Message):
    """Django API dan kitoblarni olib ko'rsatish"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/books/") as response:
            if response.status == 200:
                data = await response.json()
                books = data.get("results", data)

                if not books:
                    await message.answer("Hozircha kitoblar yo'q.")
                    return

                text = "<b>📚 Kitoblar ro'yxati:</b>\n\n"
                for book in books[:10]:
                    status = "✅" if book["is_available"] else "❌"
                    text += f"{status} <b>{book['title']}</b>\n"
                    text += f"   Muallif: {book['author_name']}\n"
                    text += f"   Mavjud: {book['available_copies']} ta\n\n"

                await message.answer(text)
            else:
                await message.answer("API ga ulanishda xatolik yuz berdi.")
